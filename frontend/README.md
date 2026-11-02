# Explorador de Relatorios

Sirva esta pasta localmente e abra o endereco exibido no navegador:

```bash
python3 -m http.server 8000 --directory frontend
```

Depois, carregue um arquivo de relatorio JSON pelo seletor da interface. O explorador nao envia dados a nenhum servidor; o arquivo e processado no navegador.

Relatorios gerados apos esta versao mostram, por no da arvore, o contexto estruturado enviado ao modelo e o trace de validacao/poda. Relatorios anteriores continuam navegaveis, mas exibem a ausencia desse trace.
