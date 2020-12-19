let H1 = document.createElement("h1");

H1.innerText = "JS created element!";

let Body = document.getElementsByTagName("body").item(0);

Body.append(H1);
