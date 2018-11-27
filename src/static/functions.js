// Funções gerais


function showLoading(){
    document.getElementById("loading_gif").style.display = "block";
}

function hideLoading(){
    document.getElementById("loading_gif").style.display = "none";
}

function show(id){
    showLoading();
    document.getElementById(id).style.display = "block";
    hideLoading();
}

function hide(id){
    document.getElementById(id).style.display = "none";
}

function reload(){
    location.reload();
}

function website_details(id){
    if(document.getElementById(id).style.display != 'none'){
        document.getElementById(id).style.display = 'none';
    }else{
        document.getElementById(id).style.display = 'block';
    }

}
