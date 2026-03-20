import Foundation
import Combine

@MainActor
final class HealthViewModel: ObservableObject {
    @Published var username: String = ""
    @Published var password: String = ""
    @Published var isLoggedIn: Bool = false
    @Published var statusMessage: String = ""
    @Published var isBusy: Bool = false

    private let authService: AuthService
    private let apiClient: HealthAPIClient
    private let healthKitManager = HealthKitManager()
    private let healthService = HealthKitService()

    init() {
        let baseURL = AppConfig.baseURL
        self.authService = AuthService(baseURL: baseURL)
        self.apiClient = HealthAPIClient(baseURL: baseURL, authService: authService)
    }

    func login() {
        guard !username.isEmpty, !password.isEmpty else {
            statusMessage = "Enter a username and password."
            return
        }

        isBusy = true
        statusMessage = "Signing in…"
        authService.login(username: username, password: password) { [weak self] result in
            DispatchQueue.main.async {
                self?.isBusy = false
                switch result {
                case .success:
                    self?.isLoggedIn = true
                    self?.statusMessage = "Signed in."
                case .failure:
                    self?.statusMessage = "Login failed. Check your credentials."
                }
            }
        }
    }

    func requestHealthAccess() {
        healthKitManager.requestAuthorization()
    }

    func syncHealthData() {
        isBusy = true
        statusMessage = "Syncing health data…"
        healthService.fetchHealthData { [weak self] result in
            guard let self = self else { return }
            DispatchQueue.main.async {
                switch result {
                case .failure(let error):
                    self.isBusy = false
                    self.statusMessage = "Health fetch failed: \(error.localizedDescription)"
                case .success(let data):
                    self.apiClient.sendHealthDataAuthenticated(data) { apiResult in
                        DispatchQueue.main.async {
                            self.isBusy = false
                            switch apiResult {
                            case .success:
                                self.statusMessage = "Health data synced."
                            case .failure(let error):
                                self.statusMessage = "Upload failed: \(error.localizedDescription)"
                            }
                        }
                    }
                }
            }
        }
    }
}
