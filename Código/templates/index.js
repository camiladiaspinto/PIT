document.getElementById("Srt").addEventListener("click", startButtonClick);
document.getElementById("Stp").addEventListener("click", stopButtonClick);
document.getElementById("Rmv").addEventListener("click",deleteButtonClick);
document.getElementById("registar-button").addEventListener("click", registarButtonClick);
document.getElementById("submit-button").addEventListener("click", submitButtonClick);


function fetchSSID_disp() {
  fetch('/ids_disponiveis')
    .then(response => response.json())
    .then(data => {
      updateTableWithSSID_disp(data);
    })
    .catch(error => {
      console.error('Erro:', error);
    });
}

function updateTableWithSSID_disp(data) {
  const table = document.getElementById("ss-disponivel");
  table.innerHTML = '<tr><th>ID Sistema</th></tr>';

  data.forEach(ss => {
    const row = document.createElement('tr');
    const idCell = document.createElement('td');
    idCell.textContent = ss;
    row.appendChild(idCell);
    table.appendChild(row);
  });
}

function verificar_id() {
  document.getElementById("submit-button").addEventListener("click", function(event) {
    event.preventDefault();
    var id_ss = document.getElementById("id_disp").value;

    fetch('/verificar-id', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        id_ss: id_ss
      })
    })
      .then(response => response.json())
      .then(data => {
        console.log(data);
        // Limpar a mensagem de erro anterior, se houver
        document.getElementById('mensagem-erro').textContent = '';
        
        // Verificar se a resposta contém uma mensagem de erro
        if (data && data.message) {
          // Exibir a mensagem de erro
          document.getElementById('mensagem-erro').textContent = data.message;
        } else {
          // Realizar qualquer ação adicional necessária após a verificação do ID
        }
      })
      .catch(error => {
        console.error('Erro:', error);
        // Exibir a mensagem de erro
        document.getElementById('mensagem-erro').textContent = 'Erro: ' + error;
      });
  });
}

function fetchIDsUtilizador() {
  fetch('/get-ids-utilizador')
    .then(response => response.json())
    .then(data => {
      updateSelectionBox(data);
    })
    .catch(error => {
      console.error('Erro:', error);
    });
}

function updateSelectionBox(data) {
  const selectBox = document.getElementById("selectID");
  selectBox.innerHTML = '';

  data.forEach(id => {
    const option = document.createElement('option');
    option.value = id[0];
    option.textContent = id[0];
    selectBox.appendChild(option);
  });

  // Recupera o sistema selecionado anteriormente e define como valor selecionado na caixa de seleção
  var selectedSystem = localStorage.getItem('selectedSystem');
  if (selectedSystem) {
    selectBox.value = selectedSystem;
  }

  // Atualize os dados do gráfico para o sistema selecionado
  fetchAmostraData();
}


function fetchAmostraData() {
  const selectedID = document.getElementById("selectID").value;
  id_ss = selectedID;
  fetch(`/get-amostra-data?id_ss=${id_ss}`)
    .then(response => response.json())
    .then(data => {
      updateTableWithAmostraData(data);

      // Armazena os valores atualizados das variáveis no armazenamento local
      localStorage.setItem('selectedSystem', id_ss);
      localStorage.setItem('timeStamp', data.humidade);
      localStorage.setItem('temperatura', data.idSelecionado);
      localStorage.setItem('humidade', data.luminosidade);
      localStorage.setItem('movimento', data.movimento);
      localStorage.setItem('luminosidade', data.temperatura);
      localStorage.setItem('idSelecionado', data.timestamp);

      // Armazena os dados históricos do sistema selecionado no armazenamento local
      var historicalData = JSON.parse(localStorage.getItem(`historicalTemperaturaData_${id_ss}`)) || [];

      // Adiciona o novo valor atual à lista de dados
      var temperaturaValue = parseFloat(data.temperatura);
      var timeStampStr = data.timeStamp;
      var dateStr = timeStampStr.substr(0, 10);
      var timeStr = timeStampStr.substr(-8);
      var timeStamp = new Date(dateStr + "T" + timeStr).getTime();

      // Cria um objeto de dados para o novo valor
      var newData = {
        date: timeStamp,
        value: temperaturaValue,
        bullet: true
      };

      // Adiciona o novo valor apenas se a lista de dados históricos estiver vazia ou o valor for mais recente
      if (historicalData.length === 0 || timeStamp > historicalData[historicalData.length - 1].date) {
        historicalData.push(newData);
      }

      // Define limite de 6 meses (em milissegundos)
      var sixMonthsLimit = 6 * 30 * 24 * 60 * 60 * 1000;

      // Remove os dados mais antigos com base no limite de 6 meses
      var sixMonthsAgo = timeStamp - sixMonthsLimit;
      historicalData = historicalData.filter(function(item) {
        return item.date >= sixMonthsAgo;
      });

      // Armazena a lista atualizada de dados históricos no armazenamento local para o sistema selecionado
      localStorage.setItem(`historicalTemperaturaData_${id_ss}`, JSON.stringify(historicalData));

      // Atualiza os dados do gráfico apenas com os dados do sistema selecionado
      updateChart(historicalData);
    })
    .catch(error => {
      console.error('Erro:', error);
    });
}


function updateChart(selectedID) {
  // Limpar os dados existentes nos gráficos de temperatura, humidade, luminosidade e movimento
  seriesTemperatura.data.clear();
  seriesHumidade.data.clear();
  seriesLuminosidade.data.clear();
  seriesMovimento.data.clear();

  // Obter os dados históricos do armazenamento local para o sistema selecionado
  var historicalDataTemperatura = JSON.parse(localStorage.getItem(`historicalTemperaturaData_${selectedID}`));
  var historicalDataHumidade = JSON.parse(localStorage.getItem(`historicalHumidadeData_${selectedID}`));
  var historicalDataLuminosidade = JSON.parse(localStorage.getItem(`historicalLuminosidadeData_${selectedID}`));
  var historicalDataMovimento = JSON.parse(localStorage.getItem(`historicalMovimentoData_${selectedID}`));

  if (historicalDataTemperatura) {
    // Adicionar os dados históricos de temperatura ao gráfico de temperatura
    seriesTemperatura.data.setAll(historicalDataTemperatura);
  }
  if (historicalDataHumidade) {
    // Adicionar os dados históricos de humidade ao gráfico de humidade
    seriesHumidade.data.setAll(historicalDataHumidade);
  }
  if (historicalDataLuminosidade) {
    // Adicionar os dados históricos de luminosidade ao gráfico de luminosidade
    seriesLuminosidade.data.setAll(historicalDataLuminosidade);
  }
  if (historicalDataMovimento) {
    // Adicionar os dados históricos de movimento ao gráfico de movimento
    seriesMovimento.data.setAll(historicalDataMovimento);
  }

  // Obter os dados mais recentes para o sistema selecionado
  var temperaturaValue = parseFloat(localStorage.getItem('temperatura'));
  var humidadeValue = parseFloat(localStorage.getItem('humidade'));
  var luminosidadeValue = parseFloat(localStorage.getItem('luminosidade'));
  var movimentoValue = parseFloat(localStorage.getItem('movimento'));
  var timeStampStr = localStorage.getItem('timeStamp');
  var dateStr = timeStampStr.substr(0, 10);
  var timeStr = timeStampStr.substr(-8);
  var timeStamp = new Date(dateStr + "T" + timeStr).getTime();

  // Adicionar o novo valor atual aos gráficos correspondentes
  seriesTemperatura.data.push({
    date: timeStamp,
    value: temperaturaValue,
    bullet: true
  });
  seriesHumidade.data.push({
    date: timeStamp,
    value: humidadeValue,
    bullet: true
  });
  seriesLuminosidade.data.push({
    date: timeStamp,
    value: luminosidadeValue,
    bullet: true
  });
  seriesMovimento.data.push({
    date: timeStamp,
    value: movimentoValue,
    bullet: true
  });

  chart.appear(1000, 100);
}













//               Funções admin                   //

function startButtonClick() {
  var samplingPeriod = document.getElementById("amostragem").value;
  fetch('/start', {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json'
      },
      body: JSON.stringify({
          action: 'start',
          'sampling_period': samplingPeriod
      })
  })
  .then(response => response.json())
  .then(data => {
      console.log(data);
  });
}

function stopButtonClick() {
  fetch('/stop', {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json'
      },
      body: JSON.stringify({
          action: 'stop'
      })
  })
  .then(response => response.json())
  .then(data => {
      console.log(data);
  });
}

function registarButtonClick(event) {
event.preventDefault();
  var email = document.getElementById("email").value;
  var password = document.getElementById("password").value;

  fetch('/registar', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      action: 'registar',
      email: email,
      password: password
    })
  })
  .then(response => response.json())
  .then(data => {
    console.log(data);
    var messageElement = document.getElementById("message");
    messageElement.innerText = data.message;
  });
}

function submitButtonClick(event) {
  event.preventDefault();
  var email = document.getElementById("email").value;
  var palavrapasse = document.getElementById("password").value;

  fetch('/formulario', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      action: 'submit',
      email: email,
      palavrapasse: palavrapasse,
    })
  })
  .then(response => response.json())
  .then(data => {
    console.log(data);
    if (data.message === 'pagina admin') {
      window.location.href = "/pagina-administrador";
    }
    else if (data.message === 'pagina utilizador') {
      window.location.href = "/pagina-user";
    }
    var messageElement = document.getElementById("message");
    messageElement.innerText = data.message;
  });
}

function fetchSSID() {
  fetch('/get-ss-ids')
    .then(response => response.json())
    .then(data => {
      updateTableWithSSID(data);
    })
    .catch(error => {
      console.error('Erro:', error);
    });
}

function updateTableWithSSID(data) {
  const table = document.getElementById("ss-table");
  table.innerHTML = '<tr><th>IDs Sistema</th></tr>';
  // Remova todas as linhas anteriores (exceto o cabeçalho)
  data.forEach(ss => {
    const row = document.createElement('tr');
    const idCell = document.createElement('td');
    idCell.textContent = ss[0];
    row.appendChild(idCell);
    table.appendChild(row);
  });

}

function fetchutilizadores() {
  fetch('/get-utilizador')
    .then(response => response.json())
    .then(data => {
      updateTableWithUtilizador(data);
    })
    .catch(error => {
      console.error('Erro:', error);
    });
}


function updateTableWithUtilizador(data) {
  const table = document.getElementById("utilizadores-table");
  table.innerHTML = '<tr><th>ID Utilizador</th><th>Email</th></tr>';
  
  data.forEach(utilizador => {
    const row = document.createElement('tr');
    const idCell = document.createElement('td');
    idCell.textContent = utilizador.id_utilizador;
    const emailCell = document.createElement('td');
    emailCell.textContent = utilizador.email;
    row.appendChild(idCell);
    row.appendChild(emailCell);
    table.appendChild(row);
  });

}



function deleteButtonClick(){
    var id_ss = document.getElementById("ss-id-to-delete").value;
    fetch('/delete_ss', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        action: ' remove',
        'id_ss' :  id_ss
      })
    })
      .then(response => response.json())
      .then(data => {
      console.log(data);
      location.reload(true);
  });
}
