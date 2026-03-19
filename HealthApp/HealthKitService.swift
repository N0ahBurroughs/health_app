import Foundation
import HealthKit

struct HealthData {
    let heartRate: Double
    let hrv: Double
    let sleepHours: Double
    let restingHeartRate: Double
}

final class HealthKitService {
    private let healthStore: HKHealthStore
    private let calendar: Calendar

    init(healthStore: HKHealthStore = HKHealthStore(), calendar: Calendar = .current) {
        self.healthStore = healthStore
        self.calendar = calendar
    }

    enum ServiceError: Error {
        case dataNotAvailable(String)
    }

    func fetchHealthData(completion: @escaping (Result<HealthData, Error>) -> Void) {
        guard HKHealthStore.isHealthDataAvailable() else {
            completion(.failure(ServiceError.dataNotAvailable("Health data is not available on this device.")))
            return
        }

        let group = DispatchGroup()

        var latestHeartRate: Double?
        var latestHRV: Double?
        var sleepHours: Double?
        var restingHeartRate: Double?
        var firstError: Error?

        group.enter()
        fetchLatestHeartRate { result in
            defer { group.leave() }
            switch result {
            case .success(let value):
                latestHeartRate = value
            case .failure(let error):
                firstError = firstError ?? error
            }
        }

        group.enter()
        fetchLatestHRV { result in
            defer { group.leave() }
            switch result {
            case .success(let value):
                latestHRV = value
            case .failure(let error):
                firstError = firstError ?? error
            }
        }

        group.enter()
        fetchSleepHoursLastNight { result in
            defer { group.leave() }
            switch result {
            case .success(let value):
                sleepHours = value
            case .failure(let error):
                firstError = firstError ?? error
            }
        }

        group.enter()
        fetchRestingHeartRate { result in
            defer { group.leave() }
            switch result {
            case .success(let value):
                restingHeartRate = value
            case .failure(let error):
                firstError = firstError ?? error
            }
        }

        group.notify(queue: .main) {
            if let error = firstError {
                completion(.failure(error))
                return
            }

            guard let heartRate = latestHeartRate,
                  let hrv = latestHRV,
                  let sleep = sleepHours,
                  let resting = restingHeartRate else {
                completion(.failure(ServiceError.dataNotAvailable("Missing one or more HealthKit values.")))
                return
            }

            completion(.success(HealthData(
                heartRate: heartRate,
                hrv: hrv,
                sleepHours: sleep,
                restingHeartRate: resting
            )))
        }
    }

    private func fetchLatestHeartRate(completion: @escaping (Result<Double, Error>) -> Void) {
        guard let heartRateType = HKQuantityType.quantityType(forIdentifier: .heartRate) else {
            completion(.failure(ServiceError.dataNotAvailable("Heart rate type is unavailable.")))
            return
        }

        let sort = NSSortDescriptor(key: HKSampleSortIdentifierEndDate, ascending: false)
        let query = HKSampleQuery(sampleType: heartRateType,
                                  predicate: nil,
                                  limit: 1,
                                  sortDescriptors: [sort]) { _, samples, error in
            if let error = error {
                completion(.failure(error))
                return
            }

            guard let sample = samples?.first as? HKQuantitySample else {
                completion(.failure(ServiceError.dataNotAvailable("No heart rate samples found.")))
                return
            }

            let unit = HKUnit.count().unitDivided(by: HKUnit.minute())
            completion(.success(sample.quantity.doubleValue(for: unit)))
        }

        healthStore.execute(query)
    }

    private func fetchLatestHRV(completion: @escaping (Result<Double, Error>) -> Void) {
        guard let hrvType = HKQuantityType.quantityType(forIdentifier: .heartRateVariabilitySDNN) else {
            completion(.failure(ServiceError.dataNotAvailable("HRV type is unavailable.")))
            return
        }

        let sort = NSSortDescriptor(key: HKSampleSortIdentifierEndDate, ascending: false)
        let query = HKSampleQuery(sampleType: hrvType,
                                  predicate: nil,
                                  limit: 1,
                                  sortDescriptors: [sort]) { _, samples, error in
            if let error = error {
                completion(.failure(error))
                return
            }

            guard let sample = samples?.first as? HKQuantitySample else {
                completion(.failure(ServiceError.dataNotAvailable("No HRV samples found.")))
                return
            }

            let unit = HKUnit.secondUnit(with: .milli)
            completion(.success(sample.quantity.doubleValue(for: unit)))
        }

        healthStore.execute(query)
    }

    private func fetchSleepHoursLastNight(completion: @escaping (Result<Double, Error>) -> Void) {
        guard let sleepType = HKCategoryType.categoryType(forIdentifier: .sleepAnalysis) else {
            completion(.failure(ServiceError.dataNotAvailable("Sleep analysis type is unavailable.")))
            return
        }

        let interval = lastNightInterval()
        let predicate = HKQuery.predicateForSamples(withStart: interval.start, end: interval.end, options: .strictStartDate)

        let sort = NSSortDescriptor(key: HKSampleSortIdentifierStartDate, ascending: true)
        let query = HKSampleQuery(sampleType: sleepType,
                                  predicate: predicate,
                                  limit: HKObjectQueryNoLimit,
                                  sortDescriptors: [sort]) { _, samples, error in
            if let error = error {
                completion(.failure(error))
                return
            }

            guard let samples = samples as? [HKCategorySample], !samples.isEmpty else {
                completion(.failure(ServiceError.dataNotAvailable("No sleep samples found for last night.")))
                return
            }

            let asleepValues: Set<Int> = [
                HKCategoryValueSleepAnalysis.asleep.rawValue,
                HKCategoryValueSleepAnalysis.asleepCore.rawValue,
                HKCategoryValueSleepAnalysis.asleepDeep.rawValue,
                HKCategoryValueSleepAnalysis.asleepREM.rawValue
            ]

            let totalSeconds = samples.reduce(0.0) { partial, sample in
                guard asleepValues.contains(sample.value) else { return partial }
                return partial + sample.endDate.timeIntervalSince(sample.startDate)
            }

            completion(.success(totalSeconds / 3600.0))
        }

        healthStore.execute(query)
    }

    private func fetchRestingHeartRate(completion: @escaping (Result<Double, Error>) -> Void) {
        guard let restingType = HKQuantityType.quantityType(forIdentifier: .restingHeartRate) else {
            completion(.failure(ServiceError.dataNotAvailable("Resting heart rate type is unavailable.")))
            return
        }

        let oneDayAgo = calendar.date(byAdding: .day, value: -1, to: Date()) ?? Date().addingTimeInterval(-86400)
        let predicate = HKQuery.predicateForSamples(withStart: oneDayAgo, end: Date(), options: .strictStartDate)

        let query = HKStatisticsQuery(quantityType: restingType,
                                      quantitySamplePredicate: predicate,
                                      options: [.discreteAverage]) { _, statistics, error in
            if let error = error {
                completion(.failure(error))
                return
            }

            guard let quantity = statistics?.averageQuantity() else {
                completion(.failure(ServiceError.dataNotAvailable("No resting heart rate samples found.")))
                return
            }

            let unit = HKUnit.count().unitDivided(by: HKUnit.minute())
            completion(.success(quantity.doubleValue(for: unit)))
        }

        healthStore.execute(query)
    }

    private func lastNightInterval() -> (start: Date, end: Date) {
        let now = Date()
        let todayStart = calendar.startOfDay(for: now)

        guard let yesterday = calendar.date(byAdding: .day, value: -1, to: todayStart),
              let start = calendar.date(bySettingHour: 18, minute: 0, second: 0, of: yesterday),
              let end = calendar.date(bySettingHour: 12, minute: 0, second: 0, of: todayStart) else {
            return (start: now.addingTimeInterval(-43200), end: now)
        }

        return (start: start, end: end)
    }
}
