/* Chatbot widget minimal
   - crea un widget flotante
   - envía mensajes a /chatbot/api/
   - muestra respuestas y botones para agregar productos
*/
(function(){
  // CSS rápido
  const style = document.createElement('style');
  style.innerHTML = `
    .bm-chatbot-button{position:fixed;right:20px;bottom:20px;background:#2b8a3e;color:#fff;border-radius:50%;width:60px;height:60px;border:none;cursor:pointer;z-index:9999;font-size:24px}
    .bm-chatbot-panel{position:fixed;right:20px;bottom:90px;width:320px;height:420px;background:#fff;border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,0.2);z-index:9999;display:flex;flex-direction:column;overflow:hidden}
    .bm-chatbot-header{background:#2b8a3e;color:#fff;padding:10px;font-weight:600}
    .bm-chatbot-messages{flex:1;padding:10px;overflow:auto;font-size:14px}
    .bm-chatbot-input{display:flex;padding:8px;border-top:1px solid #eee}
    .bm-chatbot-input input{flex:1;padding:8px;border:1px solid #ddd;border-radius:6px}
    .bm-chatbot-input button{margin-left:8px;padding:8px 12px;background:#2b8a3e;color:#fff;border:none;border-radius:6px}
    .bm-msg{margin-bottom:10px}
    .bm-msg.user{text-align:right}
    .bm-msg .bubble{display:inline-block;padding:8px 10px;border-radius:8px;max-width:85%}
    .bm-msg.user .bubble{background:#e6ffe9}
    .bm-msg.bot .bubble{background:#f1f1f1}
    .bm-product-item{border:1px solid #eee;padding:8px;margin:6px 0;border-radius:6px;display:flex;justify-content:space-between;align-items:center}
  `;
  document.head.appendChild(style);

  function getCookie(name) {
    const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return v ? v.pop() : '';
  }

  // Root
  const root = document.createElement('div');
  document.body.appendChild(root);

  const btn = document.createElement('button');
  btn.className='bm-chatbot-button';
  btn.textContent='💬';
  document.body.appendChild(btn);

  const panel = document.createElement('div');
  panel.className='bm-chatbot-panel';
  panel.style.display='none';
  panel.innerHTML = `
    <div class="bm-chatbot-header">Asistente BiomeMarket <button id="bm-open-cart" style="float:right;background:#fff;color:#2b8a3e;border:none;padding:6px 8px;border-radius:6px;cursor:pointer">Carrito</button></div>
    <div class="bm-chatbot-messages" id="bm-messages"></div>
    <div class="bm-chatbot-input">
      <input id="bm-input" placeholder="Escribe algo... (ej: buscar tomate, ver mi carrito)"> 
      <button id="bm-send">Enviar</button>
    </div>
  `;
  document.body.appendChild(panel);

  const messages = panel.querySelector('#bm-messages');
  const input = panel.querySelector('#bm-input');
  const send = panel.querySelector('#bm-send');

  btn.addEventListener('click', ()=>{
    panel.style.display = panel.style.display === 'none' ? 'flex' : 'none';
  });

  function appendMessage(text, who='bot'){ 
    const div = document.createElement('div');
    div.className = 'bm-msg '+who;
    const bubble = document.createElement('div');
    bubble.className='bubble';
    bubble.textContent = text;
    div.appendChild(bubble);
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  function renderProductos(productos){
    if(!productos || productos.length===0){ appendMessage('No encontré productos.', 'bot'); return; }
    productos.forEach(p=>{
      const el = document.createElement('div');
      el.className='bm-product-item';
      el.innerHTML = `<div><strong>${p.nombre}</strong><div style="font-size:12px;color:#666">Precio: ${p.precio} • Stock: ${p.stock} • id:${p.id}</div></div>`;
      const btnAdd = document.createElement('button');
      btnAdd.textContent='Agregar';
      btnAdd.addEventListener('click', ()=>{
        sendMessage(`agregar 1 ${p.id}`); // formato simple: agregar 1 <id>
      });
      el.appendChild(btnAdd);
      messages.appendChild(el);
    });
    messages.scrollTop = messages.scrollHeight;
  }

  async function sendMessage(msg){
    if(!msg || !msg.trim()) return;
    appendMessage(msg, 'user');
    input.value='';
    try{
      const csrftoken = getCookie('csrftoken');
      const res = await fetch('/chatbot/api/', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({message: msg})
      });
      const data = await res.json();
      if(data.type === 'productos'){
        renderProductos(data.productos);
      } else if(data.type === 'carrito'){
        if(data.items.length===0) appendMessage('Tu carrito está vacío.', 'bot');
        else{
          data.items.forEach(it=>{
            appendMessage(`${it.nombre} x${it.cantidad} — $${it.subtotal}`, 'bot');
          });
          appendMessage(`Total: $${data.total}`, 'bot');
        }
      } else if(data.type === 'texto'){
        appendMessage(data.message, 'bot');
      } else {
        appendMessage(JSON.stringify(data), 'bot');
      }
    }catch(err){
      appendMessage('Error de conexión con el servidor.', 'bot');
      console.error(err);
    }
  }

  send.addEventListener('click', ()=>sendMessage(input.value));
  input.addEventListener('keydown',(e)=>{ if(e.key==='Enter'){ sendMessage(input.value); } });

  // botón para ir al carrito desde el widget
  const openCartBtn = panel.querySelector('#bm-open-cart');
  if(openCartBtn){
    openCartBtn.addEventListener('click', ()=>{
      try{ window.location.href = '/carrito/'; }catch(e){ console.error('No se pudo redirigir al carrito', e); }
    });
  }

  // Mensaje inicial con saludo muy amable
  appendMessage('¡Hola! Bienvenido a BiomeMarket — es un gusto atenderte. Puedo buscar productos y mostrar tu carrito. Usa ejemplos como: "buscar tomate" o "ver mi carrito". También puedes pulsar el botón "Carrito" arriba para ir directamente al carrito de compras.', 'bot');

})();
