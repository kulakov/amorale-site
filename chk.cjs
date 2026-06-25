const fs=require("fs");
const h=fs.readFileSync("index.html","utf8");
const m=h.match(/const DATA=(\[.*?\]);\s*\nlet view/s);
if(\!m){console.log("DATA not matched");process.exit(1);}
const d=JSON.parse(m[1]);
console.log("DATA rows:",d.length,"sample:",JSON.stringify(d[0]));
console.log("JS template intact:",h.includes("author.today/work/${r[5]}"));
console.log("ends ok:",h.trimEnd().endsWith("</html>"));
