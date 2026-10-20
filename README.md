# Backend de controle de lanche escolar

## Configuração

Instale as dependências:

```powershell
python -m pip install -r requirements.txt
```

Crie o banco e a tabela executando `schema.sql` no MySQL. O backend conecta por
padrão a `localhost` com o usuário `root` e senha vazia. Para configurar outras
credenciais, defina `DB_HOST`, `DB_USER` e `DB_PASSWORD` no ambiente antes de
iniciar a aplicação.

## Execução

```powershell
python app.py
```

Abra `http://localhost:5000` no computador ou `http://<IP-do-computador>:5000`
no celular conectado à mesma rede Wi-Fi. A interface usa a câmera traseira para
ler QR Codes e verifica os registros no backend quando online.

O acesso à câmera em celulares requer um contexto seguro (HTTPS). Para uso na
rede local, sirva a aplicação por HTTPS; navegadores normalmente não permitem
acesso à câmera em endereços HTTP com IP local. O áudio de confirmação também
pode depender de uma interação inicial do usuário, por isso inicie a câmera pelo
botão da interface.

Quando offline, os IDs são guardados no `localStorage` do dispositivo sob a
chave `lanches_hoje` e a lista é reiniciada na virada do dia local. Esses
registros não são sincronizados automaticamente com o servidor.

## API

O endpoint `POST /verificar_qr` também pode ser chamado diretamente:

```json
{
  "id_aluno": "12345"
}
```

O endpoint retorna `status: "sucesso"` e libera o lanche se ainda não houver
registro para o aluno na data atual; se já houver, retorna
`status: "bloqueado"`.

## Carteirinhas físicas

O script `gerar_carteirinhas.py` gera PNGs de 1004 × 638 pixels a 300 DPI,
com QR Code contendo somente o ID de matrícula. Edite a lista
`alunos_demonstracao` com os dados dos estudantes e execute:

```powershell
python gerar_carteirinhas.py
```

Os arquivos serão salvos em `carteirinhas_fisicas/`. O QR Code usa correção de
erro nível H, que recupera aproximadamente até 30% dos dados do código sob
danos, desde que o padrão e os marcadores de leitura permaneçam reconhecíveis.
