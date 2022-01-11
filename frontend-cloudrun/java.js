const queryString = window.location.search;
console.log(queryString);
const urlParams = new URLSearchParams(queryString);
const token = urlParams.get('token')
const obj = {token:token}
const data = JSON.stringify(obj)
        
        fetch("GATEWAYURL", {
        method: "POST",
        credentials: "include",
        headers: {'Content-Type': 'application/json'},
        body: data
        }).then(res => {
            console.log("Data sent", data, "Request complete!", res);
        });