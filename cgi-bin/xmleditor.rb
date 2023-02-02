#!/usr/bin/env ruby
require 'cgi'
require 'json'

xml = "<list><item label='one'/><item label='two'/></list>"

def html(xml)
    <<~HTML
    <!DOCTYPE HTML>
    <html>
        <head>
            <script type="text/javascript" src="/web/js/jquery-3.2.1.min.js"></script>
            <script type="text/javascript" src="/web/lib/xonomy/xonomy.js"></script>
            <link type="text/css" rel="stylesheet" href="/web/lib/xonomy/xonomy.css"/>
            <script type="text/javascript">
                function start() {
                    window.addEventListener("message", onMessage)
                    window.opener.postMessage(JSON.stringify({ready:true}),'*')
                    console.log("Start!")
                }
                function onMessage(ev) {
                    const data = JSON.parse(ev.data)
                    if (data.xml) {
                        const {xml, docSpec} = data
                        console.log("Starting editor with docSpec")
                        console.dir(docSpec)
                        const editor = document.getElementById("editor");
                        Xonomy.setMode("laic")
                        return Xonomy.render(xml, editor, docSpec);
                    }
                    console.log(`Invalid message: ${JSON.stringify(ev.data)}`)
                }
                function submit() {
                    const xml=Xonomy.harvest();
                    window.opener.postMessage(JSON.stringify({xml}),'*')
                    setTimeout( ()=> window.close(), 500)
                }
            </script>
        </head>
        <body onload="start()">
            <div id="editor"></div>
            <!--button onclick="submit()">Submit!</button-->
        </body>
    </html>
    HTML
end

cgi = CGI.new
cgi.out("text/html") { html(xml) }
