let servResponse = document.querySelector('#response')
let loader = document.getElementById('loader')
let form = document.getElementById('upload-form')


let promise = new Promise(function (resolve, reject){
document.forms.ourForm.onsubmit = function (e) {
    e.preventDefault();
    let urlInput = document.forms.ourForm.ourForm__url.value;
    // urlInput = encodeURIComponent(urlInput)
    let xhr = new XMLHttpRequest();

    //production
    xhr.open('POST', 'http://kankitsuuu.fun/locations/choose');

    // development
    // xhr.open('POST', 'http://127.0.0.1/locations/choose');
    xhr.setRequestHeader('Content-Type', 'application/json');

    xhr.onreadystatechange = function () {
        if(xhr.readyState === 4 && xhr.status === 200) {

            let resp_data = JSON.parse(xhr.responseText)
            if(resp_data['server'] === null){
                servResponse.textContent = 'Invalid URL!';
            }
            else {
                servResponse.textContent = 'Uploading';
                loader.style.display = 'inline'
                form.style.display = 'none'
                // Использовать это как ссылку-запрос на сервер
                console.log('http://' + resp_data['server'] + '/files/upload')
                resolve(resp_data)
            }
        }

    };

    let data = JSON.stringify({'url': urlInput});
    xhr.send(data);

}
});

promise.then(data =>{
    console.log(data)
    let xhr = new XMLHttpRequest();

    // production
    xhr.open('POST',  'http://' + data['server'] + '/files/upload');

    // development
    // xhr.open('POST', 'http://127.0.0.1/files/upload');

    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onreadystatechange = function (){
         if (xhr.readyState === 4 && xhr.status === 200) {
            let resp_data = JSON.parse(xhr.responseText);
             servResponse.textContent = resp_data['message'];
             servResponse.className = resp_data['message_type']
             loader.style.display = 'none';
         }

    };
    xhr.send(JSON.stringify({'url': data['url'], 'username':data['username']}));
});