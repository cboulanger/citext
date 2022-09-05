class AnystyleFinderAnnotation extends FinderAnnotation {
  static type = Annotation.TYPE.FINDER;
  static engine = Config.ENGINES.ANYSTYLE;
  static fileExtension = "ttx";
  static mimeType = "text/plain"

  constructor(content, fileName) {
    super(content, fileName);
    this.numPages = 0
  }

  /**
   * @returns {string}
   */
  toHtml() {
    // text is in "ttx" format,
    // 1) convert it to xml-style tags
    let lines = this.content.split('\n');
    let ttx_curr_tag;
    let ttx_after_blank = false
    for (let i = 0; i < lines.length; i++) {
      let line = lines[i]
      let pipe_idx = line.indexOf("|");
      let tag;
      if (pipe_idx < 0) {
        pipe_idx = 14
        line = " ".repeat(pipe_idx) + "| " + line
      }
      tag = line.slice(0, pipe_idx).trim()
      line = line.slice(pipe_idx + 1).trim()
      let text = line
      if (line === "") {
        tag = "blank"
      }
      switch (tag) {
        case "blank":
          if (ttx_curr_tag) {
            lines[i - 1] += `</${ttx_curr_tag}>`
          }
          lines[i] = "<blank></blank>"
          ttx_after_blank = true
          continue
        case "":
          tag = ttx_curr_tag || "text"
          break
        case "ref":
          tag = "reference"
          break
      }
      if (tag !== ttx_curr_tag || ttx_after_blank) {
        line = ""
        if (ttx_curr_tag && !ttx_after_blank) {
          lines[i - 1] += `</${ttx_curr_tag}>`
        }
        if (tag === "meta") {
          if (line.match(Config.REGEX.PAGE_NUMBER_IN_LINE)) {
            this.numPages++;
            line += `<div class="page-marker" data-page="${this.numPages}"></div>`;
          }
        }
        line += `<${tag}>${text}`
        ttx_curr_tag = tag
        ttx_after_blank = false
      }
      if (i === lines.length - 1) {
        if (ttx_curr_tag) {
          line += `</${ttx_curr_tag}>`
        }
      }
      lines[i] = line
    }
    let text = lines.join("\n")
    // 2) now transform xml markup to HTML
    return super._markupToHtml(text);
  }

  loadFromHtml(html) {
    let markedUpText = html
      .replace(Config.REGEX.DIV, "")
      .replace(Config.REGEX.BR, "\n")
      .replace(Config.REGEX.DATA_TAG_SPAN, "<$1>$2</$1>")
    let currentTag;
    let xmlLines = markedUpText.split("\n")
    let ttxLines = [];
    let lastTagBeforeBlank;
    for (let xmlLine of xmlLines) {
      // replace tags with prefix
      let ttxLine = xmlLine.replace(
        /^(.*)<([^/>]+)>(.*)$/,
        (m, prefix, tag, suffix) => {
          if (tag === "reference") {
            tag = "ref"
          }
          if (tag === "blank") {
            lastTagBeforeBlank = currentTag
          }
          if (currentTag && tag === currentTag) {
            tag = ""
          } else {
            tag = tag || lastTagBeforeBlank || "text"
            currentTag = tag
            lastTagBeforeBlank = null
          }
          return tag.padEnd(14, " ") + "| " + prefix + suffix
        }
      );
      // no tag found
      if (ttxLine === xmlLine) {
        ttxLine = " ".repeat(14) + "| " + xmlLine
      }
      ttxLine = ttxLine.replace(/<\/?[^>]+>/g, "");
      ttxLines.push(ttxLine)
    }
    if (ttxLines.slice(-1).pop().startsWith("blank")) {
      ttxLines.pop()
    }
    markedUpText = ttxLines.join("\n").trim()
    this.content = Annotation.removeXmlEntities(markedUpText)
    return markedUpText
  }

  export() {
    return this.content;
  }

  extractReferences() {
    let lines = this.getContent().split("\n")
    let in_ref = false
    function* extractRefs(lines) {
      for (let line of lines) {
        let m = line.match(/^(\S*)\s+\| ?(.*)/)
        if (!m) {
          continue
        }
        let label = m[1].trim()
        let text = m[2].trim()
        switch (label) {
          case "ref":
            in_ref = true
            yield text + " "
            break
          case "":
            if (in_ref) {
              yield text + " "
            }
            break
          default:
            if (in_ref) {
              yield "\n"
            }
            in_ref = false;
        }
      }
    }
    let refs = "";
    for (let line of extractRefs(lines)) {
      refs += line
    }
    return refs
  }

  toParserAnnotation() {
    return new AnystyleParserAnnotation(this.extractReferences(), this.getFileName().replace(/.ttx/, ".xml"))
  }

  toFinderAnnotation() {
    return this;
  }
}

class AnystyleParserAnnotation extends ParserAnnotation {
  static type = Annotation.TYPE.PARSER;
  static engine = Config.ENGINES.ANYSTYLE;
  static fileExtension = "xml";
  static mimeType = "text/xml"

  constructor(content, fileName) {
    super(content, fileName);
    this.load(content)
  }

  load(content) {
    if (content.startsWith("<?xml")) {
      let lines = content.split("\n");
      //remove xml declaration and root node
      lines.splice(0, 2);
      lines.splice(-1, 1);
      content = lines
        .map(line => line.trim())
        .join("");
      // remove enclosing <sequence>tags
      content = content
        .replace(/ *<sequence> */g, "")
        .replace(/ *<\/sequence> */g, "\n")
    }
    this.content = content.trim()
    this.numRefs = content.split("\n").length
  }

  export() {
    let textToExport = this.content
      .split("\n")
      .map(line => `<sequence>${line}</sequence>`)
      .map(line => line.replace(/(<\/[^>]+>)([^<]*)(<[^>/]+>)/g, "$2$1$3"))
      .join("\n").trim();
    return `<?xml version="1.0" encoding="utf-8"?>\n<dataset>\n${textToExport}\n</dataset>`
  }
}
