#!/usr/bin/env ruby
require 'cgi'

# params
cgi = CGI.new
model_name = cgi.params["model"].first #&.gsub!('[/.]', '')
model_type = cgi.params["type"].first #&.gsub!('[/.]', '')

if !model_name || !model_type || !Dir.exist?("Dataset/#{model_name}/anystyle/#{model_type}")
    cgi.out("text/html") { "Invalid arguments" }
else
    files = Dir.glob("Dataset/#{model_name}/anystyle/#{model_type}/*").select {|f| !f.start_with? '.' }
    files_html = files.map { |path| "<li><a href='#' onclick='select_file(\"#{path}\")'>#{File.basename(path)}</a></li>\n"}.join()
    cgi.out("type" => "text/html", "charset" => "utf-8" ) {
"<head><script> function select_file(name) {
    window.opener.postMessage(name||'','*')
    setTimeout( ()=> window.close(), 500)
}</script>
<style>body {
	font-family: 'Helvetica Neue',Helvetica,Arial,sans-serif;
	font-size: 14px;
	line-height: 1.42857143;
	color: #333;
}</style>
</head><body>" +
"<h3>Select a file</h3>" +
"<button type='button' onclick='select_file()'>Close</button>
<ul>
#{files_html}
</ul>
<button type='button' onclick='select_file()'>Close</button>
</body>"
    }
end
