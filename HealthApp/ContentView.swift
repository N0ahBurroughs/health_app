import SwiftUI

struct ContentView: View {
    @StateObject private var healthKitManager = HealthKitManager()

    var body: some View {
        VStack(spacing: 16) {
            Text("HealthKit Sync")
                .font(.title)
                .fontWeight(.semibold)

            statusText
                .multilineTextAlignment(.center)
                .foregroundColor(.secondary)

            Button(action: {
                healthKitManager.requestAuthorization()
            }) {
                Text("Sync Health Data")
                    .fontWeight(.semibold)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 12)
            }
            .buttonStyle(.borderedProminent)
            .disabled(isRequesting)

            Spacer()
        }
        .padding()
    }

    private var isRequesting: Bool {
        if case .requesting = healthKitManager.authorizationState {
            return true
        }
        return false
    }

    private var statusText: Text {
        switch healthKitManager.authorizationState {
        case .idle:
            return Text("Tap the button to request HealthKit access.")
        case .notAvailable:
            return Text("Health data is not available on this device.")
        case .requesting:
            return Text("Requesting permission…")
        case .authorized:
            return Text("Access granted. You can now read health data.")
        case .denied(let message):
            return Text("Access denied. \(message)")
        }
    }
}

#Preview {
    ContentView()
}
