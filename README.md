# 💙 MacLoving - Backend

Backend do projeto **Mac Loving**, uma plataforma pensada para casais em relacionamento à distância viverem o cotidiano juntos, mesmo estando fisicamente separados. x"

> 🚧 Projeto em desenvolvimento — ainda em fase inicial (MVP)

---

## ✨ Sobre o projeto

O Mac Loving é um SaaS que busca resolver uma dor comum:
a dificuldade de manter a sensação de presença e conexão emocional em relacionamentos à distância.

Diferente de aplicativos tradicionais de casal, o foco não é apenas guardar memórias, mas sim criar uma experiência onde o casal possa compartilhar o dia a dia em tempo real.

Com o Mac Loving, casais serão capazes:

🟢 Compartilhar presença e status em tempo real (o que estão fazendo/sentindo)
💭 Criar rituais diários de conexão
🎬 Viver experiências sincronizadas (como assistir algo juntos)
🌙 Simular momentos do cotidiano, como “ir dormir juntos”
💌 Enviar interações com valor emocional (mensagens programadas, surpresas)
📸 Registrar memórias em álbuns compartilhados (feature complementar)

Este repositório contém o backend da aplicação, responsável por autenticação, lógica de negócio, comunicação em tempo real e persistência de dados.

---

## 🚀 Tecnologias utilizadas

* Python
* FastAPI
* SQLAlchemy
* PostgreSQL
* JWT (autenticação)
* Structlog (logging estruturado)

---

## 🧠 Funcionalidades atuais

* 🔐 Sistema de autenticação com JWT
* 📁 CRUD de álbuns
* 📊 Paginação com `skip` e `limit`
* 🧾 Logging estruturado com request_id
* ⚙️ Middleware personalizado

---

## 📦 Estrutura do projeto (resumida)

```
app/
├── core/        # Configurações, segurança, logging
├── models/      # Modelos do banco
├── repositories/# Acesso ao banco (camada de dados)
├── api/         # Rotas (endpoints)
```

---

## ⚠️ Status do projeto

Esse projeto ainda está no início do desenvolvimento.

## 🎯 Próximos passos

* [ ] Implementar camada de services
* [ ] Melhorar segurança (refresh token, etc.)
* [ ] Upload de imagens
* [ ] Permissões entre usuários
* [ ] Deploy em produção


## 🤝 Contribuição

O projeto ainda está em desenvolvimento pessoal, mas feedbacks são bem-vindos!

---

## 📌 Autor

Desenvolvido por Rodney-JM por enquanto 💻
(Em constante evolução 🚀)

---
