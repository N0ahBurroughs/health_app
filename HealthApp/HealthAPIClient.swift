import Foundation

final class HealthAPIClient {
    enum APIError: Error {
        case invalidResponse
        case serverError(statusCode: Int, body: String)
        case encodingFailed
        case transport(Error)
    }

    private let baseURL: URL
    private let session: URLSession
    private let encoder: JSONEncoder

    init(baseURL: URL, session: URLSession = .shared) {
        self.baseURL = baseURL
        self.session = session
        self.encoder = JSONEncoder()
        self.encoder.dateEncodingStrategy = .iso8601
    }

    struct HealthDataPayload: Encodable {
        let userId: String
        let timestamp: Date
        let metrics: HealthMetrics

        enum CodingKeys: String, CodingKey {
            case userId = "user_id"
            case timestamp
            case metrics
        }
    }

    struct HealthMetrics: Encodable {
        let heartRate: Double
        let hrv: Double
        let sleepHours: Double
        let restingHeartRate: Double

        enum CodingKeys: String, CodingKey {
            case heartRate = "heart_rate"
            case hrv
            case sleepHours = "sleep_hours"
            case restingHeartRate = "resting_heart_rate"
        }
    }

    func sendHealthData(_ healthData: HealthData,
                        userId: String,
                        timestamp: Date = Date(),
                        maxRetries: Int = 2,
                        completion: @escaping (Result<Void, Error>) -> Void) {
        let payload = HealthDataPayload(
            userId: userId,
            timestamp: timestamp,
            metrics: HealthMetrics(
                heartRate: healthData.heartRate,
                hrv: healthData.hrv,
                sleepHours: healthData.sleepHours,
                restingHeartRate: healthData.restingHeartRate
            )
        )

        guard let body = try? encoder.encode(payload) else {
            completion(.failure(APIError.encodingFailed))
            return
        }

        var request = URLRequest(url: baseURL.appendingPathComponent("health-data"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = body

        performRequest(request, retriesRemaining: maxRetries, completion: completion)
    }

    private func performRequest(_ request: URLRequest,
                                retriesRemaining: Int,
                                completion: @escaping (Result<Void, Error>) -> Void) {
        let task = session.dataTask(with: request) { data, response, error in
            if let error = error {
                if retriesRemaining > 0 {
                    self.retry(request, retriesRemaining: retriesRemaining, completion: completion)
                } else {
                    completion(.failure(APIError.transport(error)))
                }
                return
            }

            guard let httpResponse = response as? HTTPURLResponse else {
                completion(.failure(APIError.invalidResponse))
                return
            }

            if (200...299).contains(httpResponse.statusCode) {
                completion(.success(()))
                return
            }

            let bodyText = data.flatMap { String(data: $0, encoding: .utf8) } ?? ""
            if retriesRemaining > 0 && httpResponse.statusCode >= 500 {
                self.retry(request, retriesRemaining: retriesRemaining, completion: completion)
                return
            }

            completion(.failure(APIError.serverError(statusCode: httpResponse.statusCode, body: bodyText)))
        }

        task.resume()
    }

    private func retry(_ request: URLRequest,
                       retriesRemaining: Int,
                       completion: @escaping (Result<Void, Error>) -> Void) {
        let delaySeconds = pow(2.0, Double(2 - retriesRemaining))
        DispatchQueue.global().asyncAfter(deadline: .now() + delaySeconds) {
            self.performRequest(request, retriesRemaining: retriesRemaining - 1, completion: completion)
        }
    }
}
