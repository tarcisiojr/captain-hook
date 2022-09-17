# captain-hook

POC (proof of concept - prova de conceito) para um sistema de notificação e mensageiria. 
A ideia do sistema é possibilitar o cadastro de entidades (domain) genéricos e criar fluxos para consumo dessas 
informações através de eventos. 

## Caso de Uso
Sistema A é um produtor de informações e gostaria de disponibilizar a informação para os sistemas B e C. Entretanto 
o sistema B gostaria de receber a notificação apenas de eventos x, enquanto que o sistema C gostaria de receber todos os
eventos em uma determinada condição.

Neste cenário teríamos que:
- sistema A produz a informação da entidade e os eventos x e y.
- sistema B registra um "hook" para receber apenas as notificações dos eventos x.
- sistema C registra um "hook" para receber todos os eventos.

## Uso básico das APIs

### Cadastrando o schema (schema) da entidade base que se deseja armazenar.
As apis de schema criam um contrato seguindo os padrões de JSON Schema (Open API - https://json-schema.org/)

Como exemplo, estamos criando um contrato para o armazenamento de preços para produtos. Teremos 2 propriedades, preço e o nome do produto.
```shell
curl -X 'POST' \
  'http://127.0.0.1:8000/api/v1/schemas' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "price",
  "domain_schema": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "price": {
        "type": "number"
      },
      "name": {
        "type": "string"
      }
    }
  }
}'
```
### Cadastro do dato de fato (domain)
Após cadastrar o schema, agora é possível inserir os dados da entidade definida. 
Neste exemplo, está sendo inserido o "dado." referente ao preço do produto 'Eggs'
```shell
curl -X 'POST' \
  'http://127.0.0.1:8000/api/v1/schemas/price/domains' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "domain_id": "1234567890",
  "data": {
    "name": "Eggs",
    "price": 34.99
  },
  "tags": [
    [
      "tenant-x"
    ]
  ]
}'
```

### Configurando os Hooks para disparo

Neste momento será definida a configuração para dispara de 2 webhooks, sendo:

- sistema b, só receberá eventos de alteração de preços
```shell
curl -X 'POST' \
  'http://127.0.0.1:8000/api/v1/hooks' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "type": "webhook",
  "schema_name": "price",
  "event_name": "price_changed",
  "condition": null,
  "webhook": {
    "callback_url": "https://sistema-b.com/",
    "delay_time": 0,
    "http_headers": {
      "key": "xyz"
    },
    "timeout": 3,
    "max_retries": 3
  },
  "tags": [
    "tenant-x"
  ]
}'
```
 
- sistema c, receberá o evento de alteração de preço, caso seja > 100.
```shell
curl -X 'POST' \
  'http://127.0.0.1:8000/api/v1/hooks' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "type": "webhook",
  "schema_name": "price",
  "event_name": "price_changed",
  "condition": "event.metadata.new_price > 100",
  "webhook": {
    "callback_url": "https://sistema-c.com/",
    "delay_time": 0,
    "http_headers": {
      "foo": "bar"
    },
    "timeout": 3,
    "max_retries": 3
  },
  "tags": [
    "tenant-x"
  ]
}'
```

### API de emissão de eventos
Por fim, temos a API para a produção dos eventos.
```shell
curl -X 'POST' \
  'http://127.0.0.1:8000/api/v1/schemas/price/domains/1234567890/events' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "event_name": "price_changed",
  "metadata": {
    "new_price": 200
  }
}'
```

Neste cenário, o sistema fará o disparo para o sistema B e para o sistema C.
Já o cenário abaixo, só será emitido o evento para o sistema B, pois o valor alterado foi inferior a condição criada.
```shell
curl -X 'POST' \
  'http://127.0.0.1:8000/api/v1/schemas/price/domains/1234567890/events' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "event_name": "price_changed",
  "metadata": {
    "new_price": 50
  }
}'
```

# Instalação

# TODO
[ ]