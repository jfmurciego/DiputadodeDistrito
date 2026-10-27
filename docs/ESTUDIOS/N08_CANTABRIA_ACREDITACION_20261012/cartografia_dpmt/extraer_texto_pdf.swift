import PDFKit
import Foundation
for path in CommandLine.arguments.dropFirst() {
 let doc = PDFDocument(url: URL(fileURLWithPath: path))!
 print("FILE \(path) PAGES \(doc.pageCount)")
 for i in 0..<doc.pageCount { print("PAGE \(i+1)\n\(doc.page(at:i)?.string ?? "")") }
}
