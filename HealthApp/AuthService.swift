import Foundation
import Security

final class AuthService {
    struct Tokens: Codable {
        let accessToken: String
        let refreshToken: String
        let expiresIn: TimeInterval
    }

    enum AuthError: Error {
        case invalidCredentials
        case tokenUnavailable
        case refreshFailed
        case invalidResponse
    }

    private let baseURL: URL
    private let session: URLSession

    init(baseURL: URL, session: URLSession = .shared) {
        self.baseURL = baseURL
        self.session = session
    }

    func login(username: String, password: String, completion: @escaping (Result<Void, Error>) -> Void) {
        var request = URLRequest(url: baseURL.appendingPathComponent("api/token"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = ["username": username, "password": password]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body, options: [])

        session.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }

            guard let httpResponse = response as? HTTPURLResponse,
                  let data = data else {
                completion(.failure(AuthError.invalidResponse))
                return
            }

            if httpResponse.statusCode == 401 {
                completion(.failure(AuthError.invalidCredentials))
                return
            }

            guard httpResponse.statusCode >= 200 && httpResponse.statusCode < 300 else {
                completion(.failure(AuthError.invalidResponse))
                return
            }

            guard let tokens = try? JSONDecoder().decode(Tokens.self, from: data) else {
                completion(.failure(AuthError.invalidResponse))
                return
            }

            KeychainStore.save(token: tokens.accessToken, for: "access_token")
            KeychainStore.save(token: tokens.refreshToken, for: "refresh_token")
            completion(.success(()))
        }.resume()
    }

    func withValidAccessToken(completion: @escaping (Result<String, Error>) -> Void) {
        guard let accessToken = KeychainStore.loadToken(for: "access_token") else {
            completion(.failure(AuthError.tokenUnavailable))
            return
        }

        if tokenIsExpired(accessToken) {
            refreshAccessToken { result in
                switch result {
                case .success(let newAccessToken):
                    completion(.success(newAccessToken))
                case .failure(let error):
                    completion(.failure(error))
                }
            }
        } else {
            completion(.success(accessToken))
        }
    }

    private func refreshAccessToken(completion: @escaping (Result<String, Error>) -> Void) {
        guard let refreshToken = KeychainStore.loadToken(for: "refresh_token") else {
            completion(.failure(AuthError.tokenUnavailable))
            return
        }

        var request = URLRequest(url: baseURL.appendingPathComponent("api/token/refresh"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = ["refresh_token": refreshToken]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body, options: [])

        session.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }

            guard let httpResponse = response as? HTTPURLResponse,
                  let data = data else {
                completion(.failure(AuthError.invalidResponse))
                return
            }

            guard httpResponse.statusCode >= 200 && httpResponse.statusCode < 300 else {
                completion(.failure(AuthError.refreshFailed))
                return
            }

            guard let tokens = try? JSONDecoder().decode(Tokens.self, from: data) else {
                completion(.failure(AuthError.invalidResponse))
                return
            }

            KeychainStore.save(token: tokens.accessToken, for: "access_token")
            KeychainStore.save(token: tokens.refreshToken, for: "refresh_token")
            completion(.success(tokens.accessToken))
        }.resume()
    }

    private func tokenIsExpired(_ token: String) -> Bool {
        guard let exp = jwtExpirationDate(token) else { return true }
        return exp.timeIntervalSinceNow < 60
    }

    private func jwtExpirationDate(_ token: String) -> Date? {
        let segments = token.split(separator: ".")
        guard segments.count >= 2 else { return nil }
        let payloadSegment = segments[1]
        var base64 = payloadSegment
            .replacingOccurrences(of: "-", with: "+")
            .replacingOccurrences(of: "_", with: "/")
        while base64.count % 4 != 0 { base64.append("=") }
        guard let data = Data(base64Encoded: base64) else { return nil }
        guard let json = try? JSONSerialization.jsonObject(with: data, options: []) as? [String: Any] else { return nil }
        if let exp = json["exp"] as? TimeInterval {
            return Date(timeIntervalSince1970: exp)
        }
        return nil
    }
}

enum KeychainStore {
    static func save(token: String, for key: String) {
        let data = Data(token.utf8)
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecValueData as String: data,
        ]
        SecItemDelete(query as CFDictionary)
        SecItemAdd(query as CFDictionary, nil)
    }

    static func loadToken(for key: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne,
        ]
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        guard status == errSecSuccess, let data = result as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }

    static func clearTokens() {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
        ]
        SecItemDelete(query as CFDictionary)
    }
}
