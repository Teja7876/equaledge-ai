        const askBtn = document.getElementById("ask")
const input = document.getElementById("question")
const chat = document.getElementById("chat-messages")

const API_URL = "https://equaledge-ai.equaledge1ai.workers.dev/ask"

function addMessage(text, type="ai"){

const div = document.createElement("div")
div.className = "message " + type
div.textContent = text

chat.appendChild(div)
chat.scrollTop = chat.scrollHeight

}

async function askAI(question){

addMessage(question,"user")

const thinking = document.createElement("div")
thinking.className="message ai"
thinking.textContent="Thinking..."
chat.appendChild(thinking)

try{

const res = await fetch(API_URL,{
method:"POST",
headers:{
"Content-Type":"application/json"
},
body:JSON.stringify({question})
})

const data = await res.json()

thinking.remove()

if(!data.success){
addMessage("AI request failed.")
return
}

addMessage(data.answer)

if(data.sources && data.sources.length){

const sourceBlock = document.createElement("div")
sourceBlock.className="sources"

let html="<strong>Sources:</strong><ul>"

data.sources.slice(0,3).forEach(s=>{
html+=`<li>${s.title}</li>`
})

html+="</ul>"

sourceBlock.innerHTML=html

chat.appendChild(sourceBlock)

}

}catch(err){

thinking.remove()
addMessage("Connection error.")

}

}

askBtn.addEventListener("click",()=>{

const q=input.value.trim()
if(!q) return

askAI(q)
input.value=""

})

input.addEventListener("keypress",(e)=>{
if(e.key==="Enter") askBtn.click()
})

document.querySelectorAll(".suggestion").forEach(btn=>{
btn.addEventListener("click",()=>{
input.value=btn.textContent
askBtn.click()
})
})