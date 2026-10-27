import PDFKit
import AppKit
import Foundation
let doc = PDFDocument(url: URL(fileURLWithPath: CommandLine.arguments[1]))!
let page = doc.page(at:Int(CommandLine.arguments[2])!)!
let size = page.bounds(for:.mediaBox).size
let image=page.thumbnail(of:NSSize(width:size.width*3,height:size.height*3),for:.mediaBox)
let rep=NSBitmapImageRep(data:image.tiffRepresentation!)!
try! rep.representation(using:.png,properties:[:])!.write(to:URL(fileURLWithPath:CommandLine.arguments[3]))
