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
      if (pipe_idx < 0 || !line.match(Config.REGEX)) { // replace with propert TTX regex
        // add tag formatting if missing
        pipe_idx = 14
        line = " ".repeat(pipe_idx) + "| " + line
      }
      tag = line.slice(0, pipe_idx).trim()
      line = line.slice(pipe_idx + 1).trim()
      let text = line
      if (text === "") {
        tag = "blank"
      } else {
        line = text = Utils.encodeHtmlEntities(text)
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
        // add new line
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
          // hack! this works around a deeper problem with the html -> <xml> conversion
          if (tag.startsWith("span")) {
            tag = tag.replace(/span data-tag="([^"]+)"/, "$1")
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

  toParserAnnotation() {
    return new AnystyleParserAnnotation(this.extractReferences(), this.getFileName().replace(/.ttx/, ".xml"))
  }

  toFinderAnnotation() {
    return this;
  }

  extractReferences() {
    const lines = this.getContent().replace("\r", "").split("\n")
    const footnoteLines = this.extractLabelledLines(lines, /^ref/)
    const footnotes = this.splitParagraphs(footnoteLines, true)
    const bibliographyLines = this.extractLabelledLines(lines, /^bib/)
    const bibliography = this.splitParagraphs(bibliographyLines)
    return Utils.encodeHtmlEntities(footnotes.concat(bibliography).join("\n"))
  }

  /**
   * Given an array of lines, apply a number of heuristics to infer where one paragraph starts and ends
   * @param {Array<String>} lines
   * @param isFootnote
   */
  splitParagraphs(lines, isFootnote = false) {
    if (lines.length === 0) return []
    self = this

    function* extractParagraphs(lines) {
      let output = ""
      for (let [index, line] of lines.entries()) {
        // simple heuristics - we should really have our own model for this
        let startsWithFnNumber = line.match(Config.REGEX.FOOTNOTE_NUMBER_AT_LINE_START)
        let previousEndsWithDash = index > 0 && lines[index - 1].trim().match(Config.REGEX.DASH_AT_LINE_END)
        //let previousEndsWithDot = index > 0 && lines[index - 1].trim().match(/\.$/)
        let previousEndsWithNumberOrPunctuation = index > 0 && lines[index - 1].trim().match(/[\p{N}\p{P}]$/u)
        let isLongerThanPrevious = index > 0 && line.length - lines[index - 1].length > 3
        let isNewParagraph = isFootnote ?
          (startsWithFnNumber && (isLongerThanPrevious || previousEndsWithNumberOrPunctuation)) :
          (isLongerThanPrevious && !previousEndsWithDash)
        if (isNewParagraph) {
          if (output) {
            yield output
            output = ""
          }
        }
        output += self.prepareUnwrapLine(line)
      }
      if (output) {
        yield output
      }
    }
    return Array.from(extractParagraphs(lines))
  }

  /**
   *
   * @param {Array<String>} lines
   * @param {String|RegExp} label
   * @returns {Array<String>}
   */
  extractLabelledLines(lines, label) {
    if (lines.length === 0) return []
    let inLabel = false;
    let labelledLines = [];
    for (let line of lines) {
      let l = line.match(/^(\S*)\s+\| ?(.*)/)
      if (l) {
        l[1] = l[1].trim()
        if (l[1].match(label)) {
          inLabel = true;
        } else if (l[1]) {
          inLabel = false
        }
        if (inLabel) {
          labelledLines.push(l[2])
        }
      }
    }
    return labelledLines
  }

  prepareUnwrapLine(line) {
    line = line.trim()
    if (line.match(Config.REGEX.DASH_AT_LINE_END)) {
      line = line.replace(Config.REGEX.DASH_AT_LINE_END, '')
    } else {
      line += " "
    }
    return line
  }

  /**
   * @param {Array<String>} lines
   * @param {string|RegExp} footnoteLabel
   * @return {Array<String>}
   */
  extractFootnotes(lines, footnoteLabel) {
    if (lines.length === 0) return []
    let in_ref = false
    let self = this

    function* extractRefs(lines) {
      for (let line of lines) {
        let m = line.match(/^(\S*)\s+\| ?(.*)/)
        if (!m) {
          continue
        }
        let label = m[1].trim()
        let text = self.prepareUnwrapLine(m[2])
        let isFnNum = text.match(Config.REGEX.FOOTNOTE_NUMBER_AT_LINE_START)
        // && index > 0 && lines[index-1].length < line.length // heuristic needs to be tested
        let prefix = isFnNum ? "\n" : ""
        if (label.match(footnoteLabel)) {
          in_ref = true
        } else if (label !== "") {
          in_ref = false
        }
        if (in_ref) {
          yield prefix + text
        }
      }
    }

    return Array.from(extractRefs(lines))
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
    let m = content.match(/\n/g)
    this.numRefs = m ? m.length : 0
  }

  export() {
    let textToExport = this.content
      .replace(/&nbsp;/g, " ")// hack, this needs to be solved more systematically
      .split(/\n(?=<)/g)
      .filter(line => Boolean(line.trim()))
      .map(line => `<sequence>${line}</sequence>`)
      .map(line => line.replace(/(<\/[^>]+>)([^<]*)(<[^>/]+>)/g, "$2$1$3"))
      .join("\n").trim();
    return `<?xml version="1.0" encoding="utf-8"?>\n<dataset>\n${textToExport}\n</dataset>`
  }
}
