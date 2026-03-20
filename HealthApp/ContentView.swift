import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = HealthViewModel()

    var body: some View {
        NavigationView {
            VStack(spacing: 16) {
                if viewModel.isLoggedIn {
                    loggedInView
                } else {
                    loginView
                }
            }
            .padding()
            .navigationTitle("Health Sync")
        }
    }

    private var loginView: some View {
        VStack(spacing: 12) {
            TextField("Username", text: $viewModel.username)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
                .textFieldStyle(.roundedBorder)

            SecureField("Password", text: $viewModel.password)
                .textFieldStyle(.roundedBorder)

            Button("Log In") {
                viewModel.login()
            }
            .buttonStyle(.borderedProminent)
            .disabled(viewModel.isBusy)

            Text(viewModel.statusMessage)
                .font(.footnote)
                .foregroundColor(.secondary)
        }
    }

    private var loggedInView: some View {
        VStack(spacing: 12) {
            Text("Signed in as \(viewModel.username)")
                .font(.headline)

            Button("Request Health Access") {
                viewModel.requestHealthAccess()
            }
            .buttonStyle(.bordered)

            Button("Sync Health Data") {
                viewModel.syncHealthData()
            }
            .buttonStyle(.borderedProminent)
            .disabled(viewModel.isBusy)

            Text(viewModel.statusMessage)
                .font(.footnote)
                .foregroundColor(.secondary)
        }
    }
}

#Preview {
    ContentView()
}
