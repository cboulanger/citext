class Utils {

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
      return alert(e.message);
      console.log(result)
    } finally {
      GUI.hideSpinner();
    }
    return json
  }

  static download(data, filename) {
    const file = new Blob([data], {type: 'text/xml;charset=utf-8;'});
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
