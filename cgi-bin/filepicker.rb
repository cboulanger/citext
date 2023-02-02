#!/usr/bin/env ruby
require 'cgi'

# params
cgi = CGI.new
model_name = cgi.params["model"].first #&.gsub!('[/.]', '')
model_type = cgi.params["type"].first #&.gsub!('[/.]', '')

def li(path)
    "<li><a href='#' onclick='select_file(\"#{path}\")'>#{File.basename(path)}</a></li>\n"
end

def create_document(finder_files, parser_files)
    <<~HTML
    <!DOCTYPE HTML>
    <html>
        <head>
        <script>
            function select_file(name) {
                window.opener.postMessage(name||'','*')
                setTimeout( ()=> window.close(), 500)
            }
        </script>
        <style>
            body {
                font-family: 'Helvetica Neue',Helvetica,Arial,sans-serif;
                font-size: 14px;
                line-height: 1.42857143;
                color: #333;
            }
            td, th {
                vertical-align: top;
                text-align: left;
                white-space: nowrap;
            }
        </style>
        </head>
        <body>
            <h3>Select a file</h3>
            <button type='button' onclick='select_file()'>Close</button>
            <table>
                <tr><th>Finder</th><th>Parser</th></tr>
                <tr>
                    <td><ul>#{finder_files.map { |p| li(p) }.join()}</ul></td>
                    <td><ul>#{parser_files.map { |p| li(p) }.join()}</ul></td>
                </tr>
            </table>
            <button type='button' onclick='select_file()'>Close</button>
        </body>
    </html>
    HTML
end

if !model_name || !model_type || !Dir.exist?("Dataset/#{model_name}")
    html = "Dataset '#{model_name}' does not exist"
else
    finder_files = Dir.glob("Dataset/#{model_name}/anystyle/finder/*").select {|f| !f.start_with? '.' }
    parser_files = Dir.glob("Dataset/#{model_name}/anystyle/parser/*").select {|f| !f.start_with? '.' }
    html = create_document finder_files, parser_files
end

cgi.out("type" => "text/html", "charset" => "utf-8" ) {html}
