class Utils {

  /**
   * Uploads the given file to a URL and expects a JSON response, which is returned
   * @param {File} file
   * @param {string} url
   * @returns {Promise<string>}
   */
  static async upload(file, url) {
    if (!(file instanceof File)) {
      throw new TypeError("No File object")
    }
    let formData = new FormData();
    formData.append("file", file, file.name);
    GUI.showSpinner("Uploading...");
    let result, json
    try {
      result = await fetch(url, {
        method: 'post',
        body: formData,
        headers: {"Accept": "application/json"}
      })
      json = await result.json()
    } catch (e) {
      alert(e.message); // bad, only for debugging until it works
      throw e
    } finally {
      GUI.hideSpinner();
    }
    return json
  }

  /**
   * Prompts the download of the given textual data to the users computer
   * @param {string} data
   * @param {string} filename
   * @param {string} type Defaults to "text/plain; encoding=utf-8"
   */
  static download(data, filename, type = "text/plain; encoding=utf-8") {
    const file = new Blob([data], {type});
    const a = document.createElement("a");
    const url = URL.createObjectURL(file);
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(function () {
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    }, 0);
  }

  /**
   * from https://stackoverflow.com/a/47317538
   * @param sourceXml
   * @returns {string}
   */
  static prettifyXml(sourceXml) {
    const xmlDoc = new DOMParser().parseFromString(sourceXml, 'application/xml');
    const xsltDoc = new DOMParser().parseFromString([
      // describes how we want to modify the XML - indent everything
      '<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">',
      '  <xsl:strip-space elements="*"/>',
      '  <xsl:template match="para[content-style][not(text())]">', // change to just text() to strip space in text nodes
      '    <xsl:value-of select="normalize-space(.)"/>',
      '  </xsl:template>',
      '  <xsl:template match="node()|@*">',
      '    <xsl:copy><xsl:apply-templates select="node()|@*"/></xsl:copy>',
      '  </xsl:template>',
      '  <xsl:output indent="yes"/>',
      '</xsl:stylesheet>',
    ].join('\n'), 'application/xml');

    const xsltProcessor = new XSLTProcessor();
    xsltProcessor.importStylesheet(xsltDoc);
    const resultDoc = xsltProcessor.transformToDocument(xmlDoc);
    return new XMLSerializer().serializeToString(resultDoc);
  }

  static encodeHtmlEntities(text) {
    return $(document.createElement('span')).text(text).html()
  }

  static decodeHtmlEntities(text) {
    const t = document.createElement('textarea');
    t.innerHTML = text;
    return t.value;
  }
}
