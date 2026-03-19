import Foundation
import HealthKit

final class HealthKitManager: ObservableObject {
    private let healthStore = HKHealthStore()

    @Published private(set) var authorizationState: AuthorizationState = .idle

    enum AuthorizationState: Equatable {
        case idle
        case notAvailable
        case requesting
        case authorized
        case denied(String)
    }

    func requestAuthorization() {
        guard HKHealthStore.isHealthDataAvailable() else {
            authorizationState = .notAvailable
            return
        }

        let readTypes: Set<HKObjectType> = [
            HKObjectType.quantityType(forIdentifier: .heartRate),
            HKObjectType.quantityType(forIdentifier: .heartRateVariabilitySDNN),
            HKObjectType.categoryType(forIdentifier: .sleepAnalysis),
            HKObjectType.quantityType(forIdentifier: .restingHeartRate),
            HKObjectType.workoutType()
        ].compactMap { $0 }

        authorizationState = .requesting

        healthStore.requestAuthorization(toShare: [], read: readTypes) { [weak self] success, error in
            DispatchQueue.main.async {
                if success {
                    self?.authorizationState = .authorized
                } else {
                    let message = error?.localizedDescription ?? "HealthKit authorization failed."
                    self?.authorizationState = .denied(message)
                }
            }
        }
    }
}
