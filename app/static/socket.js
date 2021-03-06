const messagesList = document.getElementById("messages");
const socket_url = new URL("socket", window.location.href);  // create url for socket
socket_url.protocol = socket_url.protocol.replace('http', 'ws');

const socket = new WebSocket(socket_url.href);     // Create WebSocket connection

function feed_server_wrapper() {
    /**
     * Func to send messages to socket
     */
    let n = 1;
    function feed_server() {
        socket.send(`Hello server ${n}`);  // send message to socket here
        n = n + 1;
        if (n === 30) { socket.send("close"); }
    }
    return feed_server
}

let messageSender = setInterval(feed_server_wrapper(), 1000); // start sending messages to server every sec

socket.addEventListener('open', function (event) {
    socket.send('Start server work!');
});

socket.addEventListener('close', (e) => {
    let mes = document.createElement("li");
    mes.innerText = "Closed";
    messagesList.append(mes);
    clearInterval(messageSender); // remove sender since socket was closed
});

// Listen for messages from server and print them
socket.addEventListener('message', function (event) {
    let mes = document.createElement("li");
    mes.innerText = event.data;
    messagesList.append(mes);
});