# Smart Fridge

Projeto desenvolvido para a disciplina de **Técnicas de Prototipagem**, com o objetivo de transformar uma geladeira convencional em uma geladeira inteligente.

O sistema utilizará câmera, sensores, visão computacional e inteligência artificial para identificar produtos presentes na geladeira, manter um inventário atualizado e oferecer funcionalidades como recomendação de receitas.

## Tecnologias atuais

O frontend está sendo desenvolvido com:

- React
- Vite
- JavaScript
- React Router

## Pré-requisitos

Para executar o projeto, é necessário ter instalado:

- Git
- Node.js
- npm

Para verificar se já estão instalados:

```bash
git --version
node -v
npm -v
```

Caso o Node.js ainda não esteja instalado, utilize uma versão LTS disponível no site oficial do Node.js.

O npm é instalado junto com o Node.js.

## Clonar o projeto

### HTTPS

```bash
git clone https://github.com/pedrodev3005/smart-fridge-app.git
```

### SSH

Para quem já possui SSH configurado no GitHub:

```bash
git clone git@github.com:pedrodev3005/smart-fridge-app.git
```

Depois, entre na pasta:

```bash
cd smart-fridge-app
```

## Instalar as dependências

Na primeira vez que executar o projeto:

```bash
npm install
```

## Executar o projeto

```bash
npm run dev
```

O Vite mostrará um endereço semelhante a:

```text
http://localhost:5173/
```

Abra esse endereço no navegador para acessar o Smart Fridge.

## Acessar pelo celular

Para disponibilizar o projeto na rede local:

```bash
npm run dev -- --host
```

O terminal mostrará algo semelhante a:

```text
Local:   http://localhost:5173/
Network: http://192.168.x.x:5173/
```

No celular, abra o endereço indicado em **Network**.

O computador e o celular precisam estar conectados à mesma rede Wi-Fi.

## Estado atual

Atualmente estão sendo desenvolvidas as seguintes interfaces:

- Início
- Inventário
- Receitas
- Status do sistema
- Identificação manual de produtos não reconhecidos

As próximas etapas incluem backend, banco de dados, visão computacional, integração com Raspberry Pi, notificações e inteligência artificial.