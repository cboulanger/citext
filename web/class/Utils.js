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
  static download(data, filename, type="text/plain; encoding=utf-8") {
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
}
