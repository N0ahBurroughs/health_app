import Foundation

enum AppConfig {
    static var baseURL: URL {
        if let devURL = loadDevConfigURL() {
            return devURL
        }
        if let urlString = Bundle.main.object(forInfoDictionaryKey: "API_BASE_URL") as? String,
           let url = URL(string: urlString) { return url }
        return URL(string: "http://127.0.0.1:8000")!
    }

    private static func loadDevConfigURL() -> URL? {
        guard let url = Bundle.main.url(forResource: "DevConfig", withExtension: "plist"),
              let data = try? Data(contentsOf: url),
              let dict = try? PropertyListSerialization.propertyList(from: data, options: [], format: nil) as? [String: Any],
              let urlString = dict["API_BASE_URL"] as? String else { return nil }
        return URL(string: urlString)
    }
}
