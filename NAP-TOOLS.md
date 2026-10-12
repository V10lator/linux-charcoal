# Ferramentas NAP e persistência do aprendizado

Os pacotes instalam as ferramentas de `firelzrd/nap/tools`, fixadas no commit
`57eccac27547244459582bde893c65a5fe2f1b04` (NAP 0.6.1). A procedência e os
SHA-256 originais constam em `nap-tools/UPSTREAM.json`.

O NAP já aprende dentro do governador de CPU idle. Esta integração preserva os
pesos aprendidos entre reinicializações e acrescenta comandos de diagnóstico e
um visualizador. Ela não acrescenta treinamento em segundo plano e não permite
concluir que haverá aumento de FPS sem medir os jogos no hardware de destino.

## Instalação automática

O pacote do kernel SteamOS e o pacote `turbodecky-tuning` para PCs instalam:

- `/usr/bin/napctl`: exportar, importar, inspecionar, salvar, restaurar e calcular
  a média dos pesos;
- `nap-state.service`: restaura no boot e salva no desligamento;
- `nap-state-save.service` e `nap-state-save.timer`: salvam a cada 30 minutos;
- `/usr/share/nap/napviz.html`: visualizador local, sem servidor;
- `/usr/share/nap/napviz/`: fontes e ferramentas para reconstruir/verificar o
  visualizador.

Os serviços e o timer são habilitados na instalação e nos upgrades. Se o kernel
em execução não possui `/sys/devices/system/cpu/nap/weights`, as unidades são
ignoradas e passam a funcionar depois do boot com um kernel compatível. O build
normal exige a interface de pesos do NAP 0.6 ou posterior; não publica um pacote
com uma interface antiga e ferramentas incompatíveis. O visualizador é gerado
com os headers e pesos do NAP efetivamente aplicado ao kernel. Apenas builds
isolados do pacote de tuning sem árvore de kernel usam o HTML upstream fixado.

Em SteamOS, o estado fica no `/var/lib/nap` persistente, com diretório `0700` e
arquivos `0600`. `state.prev` conserva o snapshot anterior. O novo snapshot é
escrito e sincronizado antes de mover o anterior. Um lock serializa operações
no seletor `weights_cpu`, inclusive entre o timer e os comandos manuais.

Antes de importar, todos os registros, dimensões, checksums e valores dos pesos
são validados. Estado de outra CPU/tabela de idle é ignorado, e o kernel rejeita
mudanças incompatíveis de formato ou modelo. Estado inválido tenta o snapshot
anterior; sem um snapshot utilizável, permanece o modelo padrão do kernel.
Upgrades não reiniciam o serviço para carregar um snapshot mais antigo sobre o
aprendizado atual. Remover o pacote para o timer, salva o estado e desabilita as
unidades, preservando os arquivos de aprendizado.

A integração não altera a seleção do governador, seus parâmetros de aprendizado,
sysctl, LRU Marie ou a política de swap existente.

## Verificação após reiniciar

```bash
cat /sys/devices/system/cpu/nap/version
systemctl status nap-state.service nap-state-save.timer --no-pager
systemctl list-timers nap-state-save.timer
sudo napctl save
sudo napctl info /var/lib/nap/state
```

`active (exited)` é normal para o serviço de restauração. O timer deve estar
ativo. Se nenhuma CPU ainda inicializou seu modelo, `napctl save` informa que
não há aprendizado para salvar e conserva os snapshots existentes.

Para visualizar, abra `/usr/share/nap/napviz.html` no navegador. Exporte um
snapshot para um arquivo que seu usuário possa ler e arraste-o para a página:

```bash
sudo napctl export /tmp/nap-state
sudo chown "$(id -un):$(id -gn)" /tmp/nap-state
```

Para interromper a persistência automática:

```bash
sudo systemctl disable --now nap-state-save.timer nap-state.service
```

## Atualizar as fontes do pacote Arch

O código auditável está em `nap-tools/`. `nap-tools.tar.gz` é um snapshot local
reproduzível, usado pelo makepkg para preservar a estrutura de diretórios e
validado por SHA-256. Após modificar as ferramentas, regenere-o com
`python3 nap-tools/make-archive.py` e atualize sua entrada em `PKGBUILD`.
Os testes conferem todo o conteúdo do arquivo contra as fontes auditáveis.
