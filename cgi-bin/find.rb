#!/usr/bin/env ruby
require 'cgi'
require 'json'
require 'anystyle'

# params
cgi = CGI.new
file_name = cgi.params["filename"].first
model_name = cgi.params["model"].first
file_path = File.join("tmp", file_name).untaint

# find refs in document
if model_name != "default"
    AnyStyle.finder.load_model File.join("Models", model_name, "finder.mod").untaint
end
ttx = AnyStyle.finder.find(file_path, format: :wapiti)[0]
    .to_s(tagged:true)
    .gsub(/Generiert durch Max\-Planck\-Institut für Rechtsgeschichte und Rechtstheorie, am ([^,]+), ([^.]+)\./,"")
    .gsub(/Das Erstellen und Weitergeben von Kopien dieses PDFs ist nicht zulässig\./,"")
    .gsub(/https:\/\/doi\.org\/[\d.\/_]+/,"")

# return to client
cgi.out("application/json") { ttx.to_json }
