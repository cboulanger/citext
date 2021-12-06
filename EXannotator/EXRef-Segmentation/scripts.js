let textLines = [];
let currentLine = 0;
let filename;
let fileExt;

const SERVER_URL = "http://127.0.0.1:8000/cgi-bin/";
const LOCAL_STORAGE = {
  MARKED_UP_TEXT: "marked_up_text",
  LAST_XML_TEXT: "anno2lastxmltext",
  TEXT_FILE_NAME: "anno2filename",
  LAST_FILE_NAME: "anno2lastfilename"
}

function emptyParameters() {
  //this parameter should be empty At each start
  textLines = [];
  currentLine = 0;
  filename = "";
  fileExt = "";
  document.getElementById("txaxml").value = "";
  document.getElementById("lblColoredText").innerHTML = "";
  document.getElementById("demo").innerHTML = "";
}

$(document).ready(loadSession);

//load last saved localstorage
function loadSession() {
  let markedUpText = localStorage.getItem(LOCAL_STORAGE.MARKED_UP_TEXT);
  let lastXmlText  = localStorage.getItem(LOCAL_STORAGE.LAST_XML_TEXT);
  let textFileName = localStorage.getItem(LOCAL_STORAGE.TEXT_FILE_NAME);
  let lastFileName = localStorage.getItem(LOCAL_STORAGE.LAST_FILE_NAME);
  let fileToLoad;
  if (textFileName) {
    let filenparts = textFileName.split(".");
    filename = filenparts.slice(0, -1).join(".");
    fileExt = filenparts.pop();
  }
  // saved xml has priority if filename hasn't changed
  if (lastXmlText && filename === lastFileName) {
    fileToLoad = new Blob([lastXmlText], {type: 'text/xml'});
  } else if (markedUpText) {
    fileToLoad = new Blob([markedUpText], {type: 'text/csv'});
  }
  if (fileToLoad) {
    loadFile(fileToLoad);
  }
}

//saved the last changes before closeing
window.onbeforeunload = function () {
  savelocalStorage();
}

function showSpinner(text) {
  $("#spinner").attr("data-text", text).addClass("is-active");
}

function hideSpinner() {
  $("#spinner").removeClass("is-active");
}

function savelocalStorage() {
  let xmlText = getXmlText();
  if (xmlText) {
    localStorage.setItem(LOCAL_STORAGE.LAST_XML_TEXT, xmlText);
  }
}

async function saveToFilesystem() {
  let data = getXmlText();
  if (!data || ! filename) return;
  savelocalStorage();
  showSpinner(`Saving ${filename}.xml to training data.`);
  let body = JSON.stringify({
    filename : `${filename}.xml`,
    type: "ref_xml",
    data
  });
  let result = await (await fetch(`${SERVER_URL}/save.py`, {
    method: 'post',
    body
  })).json();
  hideSpinner();
  if (result.error) alert(result.error);
}

function goToRefAnno() {
  window.location.href = "../EXRef-Identifier/index.html";
}

function checkfile() {
  const btnLoadFile = document.getElementById("btnUploadfile");
  emptyParameters();
  const fileToLoad = btnLoadFile.files[0];
  filename = fileToLoad.name.split('.').slice(0, -1).join(".");
  fileExt = fileToLoad.name.split('.').pop();
  if (!["xml","txt","csv"].includes(fileExt)) {
    alert("Only .xml, csv or .txt files allowed.");
    return false;
  }
  loadFile(fileToLoad);
  return true;
}

function loadFile(fileToLoad) {
  const fileReader = new FileReader();
  fileReader.onload = function (evt) {
    textLines = evt.target.result
      .replace(/<author>/g, '') // replace author tags (will be re-added later)
      .replace(/<\/author>/g, '')
      .replace(/\r/g, "")
      .split('\n')
      .filter(String); // remove empty lines
    if (fileExt === "xml") {
      if (textLines[0].includes("<?xml ")) {
        // if standard-compliant xml, remove declaration and top node
        textLines.splice(0, 2);
        textLines.splice(-1, 1);
        // remove enclosing <ref> tags
        textLines = textLines
          .map(line => line.replace(/<ref>/g,'').replace(/<\/ref>/g,''));
      }
    } else {
      // csv or txt
      if (fileExt === "csv") {
        // remove cermine layout info if exists
        textLines = textLines.map(line => line.split('\t').shift())
      }
      let tmp = textLines
        .map(line => line.trim().replace(/[-]$/,"~~HYPHEN~~"))
        .join(" ")
        .replace(/~~HYPHEN~~ /g,"")
        .replace(/&lt;/g,"<")
        .replace(/&gt;/g,">");
      textLines = [];
      for (let match of tmp.matchAll(/<ref>(.*?)<\/ref>/g)) {
        textLines.push(match[1]);
      }
    }
    if (textLines.length === 0) {
      alert("No reference content!");
      return;
    }
    // display first reference
    document.getElementById("demo").innerHTML = `${filename}: ${textLines.length} references`;
    document.getElementById("lblColoredText").innerHTML = textLines[0];
    document.getElementById("txaxml").value = textLines[0];
    document.getElementById("count").innerHTML = 1 + "/" + textLines.length;
    Translate_tags_to_color_span();
    Translate_color_span_to_tag();
    // save current filename
    localStorage.setItem(LOCAL_STORAGE.LAST_FILE_NAME, filename);
  };
  fileReader.readAsText(fileToLoad, "UTF-8");
}

async function runSegmentation(){
  let result = await (await fetch(`${SERVER_URL}segmentation.py?filename=${filename}.xml`)).json();
  if (result.error) {
    return alert(result.error);
  }
  if (! result.refs_seg) {
    return alert("Invalid response");
  }
  let fileToLoad = new Blob([result.refs_seg], {type: 'text/xml'});
  loadFile(fileToLoad);
}

function exportFile() {
  if (document.getElementById("txaxml").value) {
    let fileNameToSaveAs = filename + ".xml";
    let xml = getXmlText();
    download(xml, fileNameToSaveAs);
  }
}

function getXmlText() {
  if (!document.getElementById("txaxml").value) {
    return "";
  }
  // save currently edited reference
  textLines[currentLine] = document.getElementById("txaxml").value.replace(/\n/g, '');
  // re-add <author> tag
  for (i = 0; i < textLines.length; i++) {
    if (textLines[i].indexOf('<author>') < 0) {
      textLines[i] = add_author_tag(textLines[i]);
    }
  }
  // Rejoin the line, adding a <ref> tag, and replace special chars
  let xml = textLines
    .map(line => `<ref>${line}</ref>`)
    .join("\n")
    .replace(/(&amp;)/gm, "&")
    .replace(/(&gt;)/gm, ">")
    .replace(/(&lt;)/gm, "<")
    .replace(/(&quot;)/gm, '"')
    .replace(/(&pos;)/gm, "'");

  // create valid xml
  return `<?xml version="1.0" encoding="utf-8"?>\n<seganno>\n${xml}\n</seganno>`;
}

function download(data, filename1) {
  let file = new Blob([data], {type: 'text/xml'});
  let a = document.createElement("a"),
    url = URL.createObjectURL(file);
  a.href = url;
  a.download = filename1;
  document.body.appendChild(a);
  a.click();
  setTimeout(function () {
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  }, 0);
}

//Navigate between Lines/////////////////////////////////////
function goto_firstLine() {
  // Save the current txaxml content into arrayOfLines[currentLine] to keep changes.
  // replace \n at the end of line
  textLines[currentLine] = document.getElementById("txaxml").value.replace(/\n/g, '');
  currentLine = 0;
  updateUI();
}

function goto_prevLine() {
  textLines[currentLine] = document.getElementById("txaxml").value.replace(/\n/g, '');
  if (currentLine > 0)
    currentLine = currentLine - 1;
  else
    currentLine = textLines.length - 1;
  updateUI();
}

function goto_lastLine() {
  textLines[currentLine] = document.getElementById("txaxml").value.replace(/\n/g, '');
  currentLine = textLines.length - 1;
  updateUI();
}

function goto_nextLine() {
  textLines[currentLine] = document.getElementById("txaxml").value.replace(/\n/g, '');
  if (textLines.length - 1 > currentLine)
    currentLine = currentLine + 1;
  else currentLine = 0;
  updateUI();
}

function updateUI() {
  document.getElementById("lblColoredText").innerHTML = textLines[currentLine];
  document.getElementById("txaxml").value = textLines[currentLine];
  document.getElementById("count").innerHTML = (currentLine + 1) + "/" + textLines.length;
  Translate_tags_to_color_span();
  Translate_color_span_to_tag();
}


// keynoard shortcuts ///////////////////////////////////////////////////////
document.addEventListener('keydown', function (event) {
  // alert(event.keyCode);
  sel = window.getSelection();
  var selectedtext = sel.toString();
  if (selectedtext === '')
    return;
  if (event.keyCode === 65) {
    // alert('aa was pressed');
    ChangeColor_TranslateColor('btnauthor');
  } else if (event.keyCode === 69) {
    // alert('ee was pressed');
    ChangeColor_TranslateColor('btneditor');
  } else if (event.keyCode === 71) {
    // alert('gg was pressed');
    ChangeColor_TranslateColor('btngiven-names');
  } else if (event.keyCode === 83) {
    // alert('ss was pressed');
    ChangeColor_TranslateColor('btnsurname');
  } else if (event.keyCode === 86) {
    // alert('vv was pressed');
    ChangeColor_TranslateColor('btnvolume');
  } else if (event.keyCode === 89) {
    // alert('yy was pressed');
    ChangeColor_TranslateColor('btnyear');
  } else if (event.keyCode === 84) {
    // alert('tt was pressed');
    ChangeColor_TranslateColor('btntitle');
  } else if (event.keyCode === 79) {
    // alert('oo was pressed');
    ChangeColor_TranslateColor('btnsource');
  } else if (event.keyCode === 70) {
    // alert('ff was btnfpage');
    ChangeColor_TranslateColor('btnfpage');
  } else if (event.keyCode === 76) {
    // alert('ll was btnlpage');
    ChangeColor_TranslateColor('btnlpage');
  } else if (event.keyCode === 80) {
    // alert('pp was btnPublisher');
    ChangeColor_TranslateColor('btnPublisher');
  } else if (event.keyCode === 72) {
    // alert('hh was pressed');
    ChangeColor_TranslateColor('btnother');
  } else if (event.keyCode === 68) {
    // alert('dd was pressed');
    ChangeColor_TranslateColor('btnidentifier');
  } else if (event.keyCode === 73) {
    // alert('ii was pressed');
    ChangeColor_TranslateColor('btnissue');
  } else if (event.keyCode === 85) {
    // alert('uu was pressed');
    ChangeColor_TranslateColor('btnurl');
  } else if (event.keyCode === 82) {
    // alert('rr was pressed');
    removeTag();
  }
});

//change color in plain text then call other function to translate tags in textarea ////////
function ChangeColor_TranslateColor(sender) {
  //check text
  var coloredText = document.getElementById("lblColoredText").innerHTML;
  if (coloredText === "") {
    alert('Please Select a file');
    return;
  }
  //Get Tag Name
  var tagname;
  if (sender.value)
    tagname = sender.value;
  else
    tagname = sender;
  //Get Selection Text
  sel = window.getSelection();
  if (sel.rangeCount && sel.getRangeAt) {
    range = sel.getRangeAt(0);
  }
  // Set design mode to on
  document.designMode = "on";
  if (range) {
    sel.removeAllRanges();
    sel.addRange(range);
  }
  //Colorize text
  if (tagname === "btnauthor") {
    document.execCommand("HiliteColor", false, "#ff9681");
  } else if (tagname === "btnsurname") {
    document.execCommand("HiliteColor", false, "#ffce30");
  } else if (tagname === "btngiven-names") {
    document.execCommand("HiliteColor", false, "#aabb30");
  } else if (tagname === "btnyear") {
    document.execCommand("HiliteColor", false, "#bfb1d5");
  } else if (tagname === "btntitle") {
    document.execCommand("HiliteColor", false, "#adddcf");
  } else if (tagname === "btnsource") {
    document.execCommand("HiliteColor", false, "#abe1fd");
  } else if (tagname === "btneditor") {
    document.execCommand("HiliteColor", false, "#fed88f");
  } else if (tagname === "btnvolume") {
    document.execCommand("HiliteColor", false, "#ffff66");
  } else if (tagname === "btnother") {
    document.execCommand("HiliteColor", false, "#f4858e");
  } else if (tagname === "btnfpage") {
    document.execCommand("HiliteColor", false, "#ccff66");
  } else if (tagname === "btnlpage") {
    document.execCommand("HiliteColor", false, "#ffb3ff");
  } else if (tagname === "btnPublisher") {
    document.execCommand("HiliteColor", false, "#79d279");
  } else if (tagname === "btnissue") {
    document.execCommand("HiliteColor", false, "#659bf2");
  } else if (tagname === "btnurl") {
    document.execCommand("HiliteColor", false, "#5befdb");
  } else if (tagname === "btnidentifier") {
    document.execCommand("HiliteColor", false, "#d19bf7");
  } else {
    document.getElementById("error").innerHTML = " Button broken!";
  }
  // Set design mode to off
  document.designMode = "off";
  // ?? why??
  var currentText = document.getElementById("lblColoredText").innerHTML;
  document.getElementById("lblColoredText").innerHTML = currentText;
  Translate_color_span_to_tag();
  // Translate_tags_to_color_span();
}

function Translate_color_span_to_tag() {
  //replaces the manually added tags with colortags in lblColoredText.
  //lblColoredText Contains <span tags>
  var arrayCopyOflblText = [];
  document.getElementById("lblColoredText").innerHTML = document.getElementById("lblColoredText").innerHTML.replace(/ <\/span>/gm, "</span> ");
  arrayCopyOflblText[currentLine] = document.getElementById("lblColoredText").innerHTML;
  var openSpanValue = "";
  var tagname = "";

  //replace all

  //for surname
  openSpanValue = '<span style="background-color: rgb(255, 206, 48);">';
  while (arrayCopyOflblText[currentLine].indexOf(openSpanValue) !== -1) {
    var text1 = arrayCopyOflblText[currentLine].substr(0, arrayCopyOflblText[currentLine].indexOf(openSpanValue));
    var text2 = arrayCopyOflblText[currentLine].substr(arrayCopyOflblText[currentLine].indexOf(openSpanValue), arrayCopyOflblText[currentLine].length);
    text2 = text2.replace("</span>", "</surname>");
    arrayCopyOflblText[currentLine] = text1 + text2;
    arrayCopyOflblText[currentLine] = arrayCopyOflblText[currentLine].replace(openSpanValue, '<surname>');
  }

  //for given-names
  openSpanValue = '<span style="background-color: rgb(170, 187, 48);">';
  while (arrayCopyOflblText[currentLine].indexOf(openSpanValue) !== -1) {
    var text1 = arrayCopyOflblText[currentLine].substr(0, arrayCopyOflblText[currentLine].indexOf(openSpanValue));
    var text2 = arrayCopyOflblText[currentLine].substr(arrayCopyOflblText[currentLine].indexOf(openSpanValue), arrayCopyOflblText[currentLine].length);
    text2 = text2.replace("</span>", "</given-names>");
    arrayCopyOflblText[currentLine] = text1 + text2;
    arrayCopyOflblText[currentLine] = arrayCopyOflblText[currentLine].replace(openSpanValue, '<given-names>');
  }

  //for year
  openSpanValue = '<span style="background-color: rgb(191, 177, 213);">';
  while (arrayCopyOflblText[currentLine].indexOf(openSpanValue) !== -1) {
    var t1 = arrayCopyOflblText[currentLine].substr(0, arrayCopyOflblText[currentLine].indexOf(openSpanValue));
    var t2 = arrayCopyOflblText[currentLine].substr(arrayCopyOflblText[currentLine].indexOf(openSpanValue), arrayCopyOflblText[currentLine].length).replace("</span>", "</year>")
    arrayCopyOflblText[currentLine] = t1 + t2;
    arrayCopyOflblText[currentLine] = arrayCopyOflblText[currentLine].replace('<span style="background-color: rgb(191, 177, 213);">', '<year>');
  }
  //for title
  openSpanValue = '<span style="background-color: rgb(173, 221, 207);">'
  while (arrayCopyOflblText[currentLine].indexOf(openSpanValue) !== -1) {
    arrayCopyOflblText[currentLine] = arrayCopyOflblText[currentLine].substr(0, arrayCopyOflblText[currentLine].indexOf(openSpanValue)) + arrayCopyOflblText[currentLine].substr(arrayCopyOflblText[currentLine].indexOf(openSpanValue), arrayCopyOflblText[currentLine].length).replace("</span>", "</title>");
    arrayCopyOflblText[currentLine] = arrayCopyOflblText[currentLine].replace(openSpanValue, '<title>');
  }
  //for source
  while (arrayCopyOflblText[currentLine].indexOf('<span style="background-color: rgb(171, 225, 253);">') !== -1) {
    arrayCopyOflblText[currentLine] = arrayCopyOflblText[currentLine].substr(0, arrayCopyOflblText[currentLine].indexOf('<span style="background-color: rgb(171, 225, 253);">')) + arrayCopyOflblText[currentLine].substr(arrayCopyOflblText[currentLine].indexOf('<span style="background-color: rgb(171, 225, 253);">'), arrayCopyOflblText[currentLine].length).replace("</span>", "</source>");
    arrayCopyOflblText[currentLine] = arrayCopyOflblText[currentLine].replace('<span style="background-color: rgb(171, 225, 253);">', '<source>');
  }
  //for editor
  while (arrayCopyOflblText[currentLine].indexOf('<span style="background-color: rgb(254, 216, 143);">') !== -1) {
    arrayCopyOflblText[currentLine] = arrayCopyOflblText[currentLine].substr(0, arrayCopyOflblText[currentLine].indexOf('<span style="background-color: rgb(254, 216, 143);">')) + arrayCopyOflblText[currentLine].substr(arrayCopyOflblText[currentLine].indexOf('<span style="background-color: rgb(254, 216, 143);">'), arrayCopyOflblText[currentLine].length).replace("</span>", "</editor>");
    arrayCopyOflblText[currentLine] = arrayCopyOflblText[currentLine].replace('<span style="background-color: rgb(254, 216, 143);">', '<editor>');
  }
  //for volume
  while (arrayCopyOflblText[currentLine].indexOf('<span style="background-color: rgb(255, 255, 102);">') !== -1) {
    arrayCopyOflblText[currentLine] = arrayCopyOflblText[currentLine].substr(0, arrayCopyOflblText[currentLine].indexOf('<span style="background-color: rgb(255, 255, 102);">')) + arrayCopyOflblText[currentLine].substr(arrayCopyOflblText[currentLine].indexOf('<span style="background-color: rgb(255, 255, 102);">'), arrayCopyOflblText[currentLine].length).replace("</span>", "</volume>");
    arrayCopyOflblText[currentLine] = arrayCopyOflblText[currentLine].replace('<span style="background-color: rgb(255, 255, 102);">', '<volume>');
  }
  //fpage ================================================================
  while (arrayCopyOflblText[currentLine].indexOf('<span style="background-color: rgb(204, 255, 102);">') !== -1) {
    arrayCopyOflblText[currentLine] = arrayCopyOflblText[currentLine].substr(0, arrayCopyOflblText[currentLine].indexOf('<span style="background-color: rgb(204, 255, 102);">')) + arrayCopyOflblText[currentLine].substr(arrayCopyOflblText[currentLine].indexOf('<span style="background-color: rgb(204, 255, 102);">'), arrayCopyOflblText[currentLine].length).replace("</span>", "</fpage>");
    arrayCopyOflblText[currentLine] = arrayCopyOflblText[currentLine].replace('<span style="background-color: rgb(204, 255, 102);">', '<fpage>');//
  }
  //lpage ================================================================
  while (arrayCopyOflblText[currentLine].indexOf('<span style="background-color: rgb(255, 179, 255);">') !== -1) {
    arrayCopyOflblText[currentLine] = arrayCopyOflblText[currentLine].substr(0, arrayCopyOflblText[currentLine].indexOf('<span style="background-color: rgb(255, 179, 255);">')) + arrayCopyOflblText[currentLine].substr(arrayCopyOflblText[currentLine].indexOf('<span style="background-color: rgb(255, 179, 255);">'), arrayCopyOflblText[currentLine].length).replace("</span>", "</lpage>");
    arrayCopyOflblText[currentLine] = arrayCopyOflblText[currentLine].replace('<span style="background-color: rgb(255, 179, 255);">', '<lpage>');//
  }
  //btnPublisher ================================================================
  while (arrayCopyOflblText[currentLine].indexOf('<span style="background-color: rgb(121, 210, 121);">') !== -1) {
    arrayCopyOflblText[currentLine] = arrayCopyOflblText[currentLine].substr(0, arrayCopyOflblText[currentLine].indexOf('<span style="background-color: rgb(121, 210, 121);">')) + arrayCopyOflblText[currentLine].substr(arrayCopyOflblText[currentLine].indexOf('<span style="background-color: rgb(121, 210, 121);">'), arrayCopyOflblText[currentLine].length).replace("</span>", "</publisher>");
    arrayCopyOflblText[currentLine] = arrayCopyOflblText[currentLine].replace('<span style="background-color: rgb(121, 210, 121);">', '<publisher>');//
  }
  //other ================================================================
  openSpanValue = '<span style="background-color: rgb(244, 133, 142);">';
  tagname = 'other';
  arrayCopyOflblText = subfunction_Translate_color_span_to_tag(arrayCopyOflblText, openSpanValue, tagname);
  textLines[currentLine] = arrayCopyOflblText[currentLine];
  //issue ================================================================
  openSpanValue = '<span style="background-color: rgb(101, 155, 242);">'
  tagname = 'issue';
  arrayCopyOflblText = subfunction_Translate_color_span_to_tag(arrayCopyOflblText, openSpanValue, tagname);
  textLines[currentLine] = arrayCopyOflblText[currentLine];
  //url ================================================================
  openSpanValue = '<span style="background-color: rgb(91, 239, 219);">'
  tagname = 'url';
  arrayCopyOflblText = subfunction_Translate_color_span_to_tag(arrayCopyOflblText, openSpanValue, tagname);
  textLines[currentLine] = arrayCopyOflblText[currentLine];
  //identifier ================================================================
  openSpanValue = '<span style="background-color: rgb(209, 155, 247);">'
  tagname = 'identifier';
  arrayCopyOflblText = subfunction_Translate_color_span_to_tag(arrayCopyOflblText, openSpanValue, tagname);
  textLines[currentLine] = arrayCopyOflblText[currentLine];
  // ================================================================
  var currentText = textLines[currentLine];
  arrayCopyOflblText[currentLine] = currentText;
  // ================================================================
  currentText = add_author_tag(currentText);
  document.getElementById("txaxml").value = currentText;
}

function add_author_tag(currentText) {
  let arr = []
  let arr_open_surname = getIndicesOf('<surname>', currentText)
  let arr_close_surname = getIndicesOf('</surname>', currentText)
  let arr_open_givennames = getIndicesOf('<given-names>', currentText)
  let arr_close_givennames = getIndicesOf('</given-names>', currentText)
  let len_of_arr_open_surname = arr_open_surname.length
  let len_of_arr_open_givennames = arr_open_givennames.length

  let max_number = (len_of_arr_open_surname >= len_of_arr_open_givennames) ? len_of_arr_open_surname : len_of_arr_open_givennames

  String.prototype.splice = function (idx, rem, str) {
    return this.slice(0, idx) + str + this.slice(idx + Math.abs(rem));
  };

  for (var i = 0; i < max_number; i++) {
    arr_open_surname = getIndicesOf('<surname>', currentText)
    arr_close_surname = getIndicesOf('</surname>', currentText)
    arr_open_givennames = getIndicesOf('<given-names>', currentText)
    arr_close_givennames = getIndicesOf('</given-names>', currentText)

    if (arr_open_surname[i] !== undefined && arr_open_givennames[i] === undefined) {
      arr_open_surname = getIndicesOf('<surname>', currentText)
      currentText = currentText.splice(arr_open_surname[i], 0, "<author>");
      arr_close_surname = getIndicesOf('</surname>', currentText)
      currentText = currentText.splice(arr_close_surname[i] + 10, 0, "</author>");
    } else if (arr_open_givennames[i] !== undefined && arr_open_surname[i] === undefined) {
      arr_open_givennames = getIndicesOf('<given-names>', currentText)
      currentText = currentText.splice(arr_open_givennames[i], 0, "<author>");
      arr_close_givennames = getIndicesOf('</given-names>', currentText)
      currentText = currentText.splice(arr_close_givennames[i] + 14, 0, "</author>");
    } else {
      if (arr_open_surname[i] < arr_open_givennames[i]) {
        // surname is first tag AND givennames is second tag
        arr_open_surname = getIndicesOf('<surname>', currentText)
        currentText = currentText.splice(arr_open_surname[i], 0, "<author>");
        arr_close_givennames = getIndicesOf('</given-names>', currentText)
        currentText = currentText.splice(arr_close_givennames[i] + 14, 0, "</author>");
      } else if (arr_open_surname[i] > arr_open_givennames[i]) {
        // givennames is first tag AND surname is second tag
        arr_open_givennames = getIndicesOf('<given-names>', currentText)
        currentText = currentText.splice(arr_open_givennames[i], 0, "<author>");
        arr_close_surname = getIndicesOf('</surname>', currentText)
        currentText = currentText.splice(arr_close_surname[i] + 10, 0, "</author>");
      }
    }
  }
  return currentText;
}

function getIndicesOf(searchStr, str) {
  var searchStrLen = searchStr.length;
  if (searchStrLen === 0) {
    return [];
  }
  var startIndex = 0, index, indices = [];
  while ((index = str.indexOf(searchStr, startIndex)) > -1) {
    indices.push(index);
    startIndex = index + searchStrLen;
  }
  return indices;
}

function subfunction_Translate_color_span_to_tag(arrayCopyOflblText, openSpanValue, tagname) {
  while (arrayCopyOflblText[currentLine].indexOf(openSpanValue) !== -1) {
    var t1 = arrayCopyOflblText[currentLine].substr(0, arrayCopyOflblText[currentLine].indexOf(openSpanValue));
    var t2 = arrayCopyOflblText[currentLine].substr(arrayCopyOflblText[currentLine].indexOf(openSpanValue), arrayCopyOflblText[currentLine].length).replace("</span>", "</" + tagname + ">");
    arrayCopyOflblText[currentLine] = t1 + t2;
    arrayCopyOflblText[currentLine] = arrayCopyOflblText[currentLine].replace(openSpanValue, '<' + tagname + '>');
  }
  return arrayCopyOflblText;
}

function Translate_tags_to_color_span() {// replaces the manually added tags with colortags for lblColoredText.
  textLines[currentLine] = document.getElementById("txaxml").value;

  var textCopy = textLines;
  // //author
  // while (textCopy[currentLine].indexOf("<author>") !== -1) {
  // 	textCopy[currentLine] = textCopy[currentLine].replace("</author>", "</span>");
  // 	textCopy[currentLine] = textCopy[currentLine].replace('<author>', '<span style="background-color: rgb(255, 150, 129);">');
  // }
  //surname
  while (textCopy[currentLine].indexOf("<surname>") !== -1) {
    textCopy[currentLine] = textCopy[currentLine].replace("</surname>", "</span>");
    textCopy[currentLine] = textCopy[currentLine].replace('<surname>', '<span style="background-color: rgb(255, 206, 48);">');
  }
  //2
  while (textCopy[currentLine].indexOf('</span><span style="background-color: rgb(255, 206, 48);>') !== -1) {
    textCopy[currentLine] = textCopy[currentLine].replace('</span><span style="background-color: rgb(255, 206, 48);>', '<span style="background-color: rgb(255, 206, 48);">');
  }
  //given-names
  while (textCopy[currentLine].indexOf("<given-names>") !== -1) {
    textCopy[currentLine] = textCopy[currentLine].replace("</given-names>", "</span>");
    textCopy[currentLine] = textCopy[currentLine].replace('<given-names>', '<span style="background-color: rgb(170, 187, 48);">');
  }
  //2
  while (textCopy[currentLine].indexOf('</span><span style="background-color: rgb(170, 187, 48);">') !== -1) {
    textCopy[currentLine] = textCopy[currentLine].replace('</span><span style="background-color: rgb(170, 187, 48);">', '<span style="background-color: rgb(170, 187, 48);">');
  }
  //year
  while (textCopy[currentLine].indexOf("<year>") !== -1) {
    textCopy[currentLine] = textCopy[currentLine].replace("</year>", "</span>");
    textCopy[currentLine] = textCopy[currentLine].replace('<year>', '<span style="background-color: rgb(191, 177, 213);">');
  }
  while (textCopy[currentLine].indexOf("<title>") !== -1) {
    textCopy[currentLine] = textCopy[currentLine].replace("</title>", "</span>");
    textCopy[currentLine] = textCopy[currentLine].replace('<title>', '<span style="background-color: rgb(173, 221, 207);">');
  }
  while (textCopy[currentLine].indexOf("<source>") !== -1) {
    textCopy[currentLine] = textCopy[currentLine].replace("</source>", "</span>");
    textCopy[currentLine] = textCopy[currentLine].replace('<source>', '<span style="background-color: rgb(171, 225, 253);">');
  }
  while (textCopy[currentLine].indexOf("<editor>") !== -1) {
    textCopy[currentLine] = textCopy[currentLine].replace("</editor>", "</span>");
    textCopy[currentLine] = textCopy[currentLine].replace('<editor>', '<span style="background-color: rgb(254, 216, 143);">');
  }
  //volume
  while (textCopy[currentLine].indexOf("<volume>") !== -1) {
    textCopy[currentLine] = textCopy[currentLine].replace("</volume>", "</span>");
    textCopy[currentLine] = textCopy[currentLine].replace('<volume>', '<span style="background-color: rgb(255, 255, 102);">');
  }
  //fpage
  while (textCopy[currentLine].indexOf("<fpage>") !== -1) {
    textCopy[currentLine] = textCopy[currentLine].replace("</fpage>", "</span>");
    textCopy[currentLine] = textCopy[currentLine].replace('<fpage>', '<span style="background-color: rgb(204, 255, 102);">');//
  }
  //lpage
  while (textCopy[currentLine].indexOf("<lpage>") !== -1) {
    textCopy[currentLine] = textCopy[currentLine].replace("</lpage>", "</span>");
    textCopy[currentLine] = textCopy[currentLine].replace('<lpage>', '<span style="background-color: rgb(255, 179, 255);">');//
  }
  //lpage
  while (textCopy[currentLine].indexOf("<publisher>") !== -1) {
    textCopy[currentLine] = textCopy[currentLine].replace("</publisher>", "</span>");
    textCopy[currentLine] = textCopy[currentLine].replace('<publisher>', '<span style="background-color: rgb(121, 210, 121);">');//
  }
  // other
  while (textCopy[currentLine].indexOf("<other>") !== -1) {
    textCopy[currentLine] = textCopy[currentLine].replace("</other>", "</span>");
    textCopy[currentLine] = textCopy[currentLine].replace('<other>', '<span style="background-color: rgb(244, 133, 142);">');
  }
  // issue
  while (textCopy[currentLine].indexOf("<issue>") !== -1) {
    textCopy[currentLine] = textCopy[currentLine].replace("</issue>", "</span>");
    textCopy[currentLine] = textCopy[currentLine].replace('<issue>', '<span style="background-color: rgb(101, 155, 242);">');
  }
  // url
  while (textCopy[currentLine].indexOf("<url>") !== -1) {
    textCopy[currentLine] = textCopy[currentLine].replace("</url>", "</span>");
    textCopy[currentLine] = textCopy[currentLine].replace('<url>', '<span style="background-color: rgb(91, 239, 219);">');
  }
  // identifier
  while (textCopy[currentLine].indexOf("<identifier>") !== -1) {
    textCopy[currentLine] = textCopy[currentLine].replace("</identifier>", "</span>");
    textCopy[currentLine] = textCopy[currentLine].replace('<identifier>', '<span style="background-color: rgb(209, 155, 247);">');
  }
  document.getElementById("lblColoredText").innerHTML = textCopy[currentLine];
}

// delete function /////////////////////////////////////////////////////////////////
function removeTag() {
  let sel = window.getSelection();
  if (sel.toString() === "") {
    alert('No Selection');
    return;
  }
  if (sel.anchorNode.parentElement.toString() === "[object HTMLSpanElement]") {
    $(sel.anchorNode.parentElement).contents().unwrap();
    Translate_color_span_to_tag();
  }
}

