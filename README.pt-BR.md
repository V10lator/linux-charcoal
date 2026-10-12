# Kernel Charcoal para SteamOS - Edição Vulcano 
Antes de instalar, por favor verifique se você está no canal estável de instalação do SteamOs 

[![build](https://github.com/zarpon/linux-charcoal-vulcano/actions/workflows/push.yml/badge.svg?branch=master)](https://github.com/zarpon/linux-charcoal-vulcano/actions)

[English](README.md)

O Charcoal Vulcano é um pacote de kernel experimental para Steam Deck, Asus ROG Ally e
outros PCs portáteis AMD. Ele é construído a partir do
[`linux-neptune`](https://gitlab.steamos.cloud/jupiter/linux-integration) da
Valve, com um conjunto de alterações de agendamento, memória, I/O, Wi-Fi e
suporte específico para portáteis, todas registradas na origem da compilação.

> **Alvo atual de compilação:** a tag oficial mais recente do SteamOS da Valve
> que corresponde a `6.18.*-valve*`. O
> resolvedor procura uma tag 6.18 mais nova a cada compilação; cada release
> registra a revisão exata do código-fonte e a seleção dinâmica de patches usada.
>
> **Canal estável da master:** o instalador consulta o endpoint
> `/releases/latest` do GitHub e aceita somente uma release publicada, não draft
> e não pré-release, com tag `charcoal-6.18.*-r<run>` e os nomes de arquivos
> esperados. Se a release estável mais recente do GitHub for de outra série de
> kernel, ele falha de modo seguro; não recua para uma release 6.18 mais antiga.

## Dispositivos suportados

| Dispositivo | Status | Observação |
| --- | --- | --- |
| Steam Deck (LCD) | ✅ Testado | Alvo principal |
| Steam Deck (OLED) | ✅ Testado | Alvo principal |
| Asus ROG Ally (RC71L) | ✅ Testado | Confirmado pela comunidade |
| Outros portáteis AMD | ❓ Não testado | Informe o resultado em uma issue |

## Patches e configuração aplicados

Antes da compilação, o workflow da release resolve os componentes mantidos
abaixo. O arquivo `patch-lock.json`, incluído no arquivo da release, é o
registro oficial dos caminhos, commits, origens e valores SHA-256 exatos dos
patches usados.

| Componente | O que é aplicado no Charcoal |
| --- | --- |
| [LRU Marie](https://github.com/firelzrd/lru_marie) | Habilita o caminho de recuperação de memória LRU Marie (`CONFIG_LRU_MARIE=y`). |
| [zram-ir](https://github.com/firelzrd/zram-ir) | Adiciona o controle de recompressão imediata do zram por meio de `vm.zram_recomp_immediate`. O porte Charcoal do kernel define esse controle como `1`, portanto a escrita tenta LZ4 primário e depois ZSTD na prioridade `1`. O porte incluído fixa a compressão ZSTD do ZRAM no equivalente a `zstd --fast=1` (`-1`); `algorithm_params` do espaço de usuário não pode substituí-lo. Um *drop-in* do `zram-generator` e o `ExecStartPre` de `systemd-zram-setup@` configuram os dois algoritmos antes de `disksize`. O helper udev reafirma o sysctl e fornece um fallback seguro; ele nunca redefine um dispositivo inicializado ou swap ativo e não cria um dispositivo zram adicional. |
| [RFC AMD P-State: boost EPP por núcleo](https://lore.kernel.org/linux-pm/20260728073150.54964-2-void@manifault.com/t/#m22b425e7e2889c9656fe7422aa02d78d91a36431) | Aplica primeiro o payload canônico mais recente dos quatro patches RFC, com portas revisadas para Valve 6.18.45 como fallbacks estritos: limpeza de kernel-doc, ordenação do cache de requisições CPPC, boost EPP por núcleo recentemente ocupado e documentação. O Charcoal ativa `amd_pstate.epp_boost=1` em sua linha de comando interna por padrão; ele só atua no modo ativo baseado em MSR e pode ser desativado explicitamente com `amd_pstate.epp_boost=0` nos argumentos do boot loader. |
| [ADIOS](https://github.com/firelzrd/adios) | Adiciona o escalonador Adaptive Deadline I/O Scheduler e o torna o escalonador MQ de I/O padrão. A regra udev instalada também seleciona `adios` para dispositivos de bloco compatíveis, exceto dispositivos loop e zram. |
| [BORE Scheduler 6.8.0](https://github.com/firelzrd/bore-scheduler/tree/main/patches/testing) | Habilita o escalonador de CPU Burst-Oriented Response Enhancer (`CONFIG_SCHED_BORE=y`) por meio do porte revisado para Valve 6.18.45 do patch oficial mais recente do BORE 6.8.0. |
| [Correção de coexistência BORE sched_ext](https://github.com/firelzrd/bore-scheduler/tree/main/patches/additions) | Aplica o upstream `0002-sched-ext-coexistence-fix.patch` após o BORE. O porte local do Valve preserva o helper e acrescenta o protótipo interno exigido pela compilação estrita, sem usar fuzz. |
| [POC Selector](https://github.com/firelzrd/poc-selector) | Habilita a seleção de CPU ociosa por bitmap (`CONFIG_SCHED_POC_SELECTOR=y`) no caminho de ativação de tarefas. Usa o patch nativo 6.18 mais recente quando disponível; caso contrário, seu adaptador restrito para Valve/BORE porta a release oficial mais nova e rejeita mudanças inesperadas de hunk antes do empacotamento. |
| [Nap](https://github.com/firelzrd/nap) | Habilita o governador Neural Adaptive Predictor de CPU idle. O fragmento de configuração do Charcoal desabilita ladder, menu e teo e habilita o NAP. |
| **AMD IOMMU PerfOpt** | Em IOMMU AMD compatível, habilita automaticamente o PerfOpt para GPUs integradas elegíveis usando um domínio DMA identity; o caminho otimizado do IOMMU pode reduzir a latência de DMA. ATS/PRI/PASID/SVA não são configurados, reduzindo o isolamento de DMA do IOMMU nesse caminho; o resultado depende do hardware e da carga, sem percentual garantido. Não há opção amdgpu.iommu_perfopt para desativá-lo em tempo de execução. |

Para cada componente versionado, o resolvedor começa pela release upstream mais
recente e prioriza o patch nativo para Linux 6.18. Quando não há patch 6.18
nativo, ele tenta primeiro os bytes canônicos upstream mais novos e usa um
porte local 6.18 revisado somente como fallback estrito após falha de aplicação.
O `patch-lock.json` registra a fonte selecionada e qualquer fallback. O
BORE é acompanhado a partir dos diretórios de teste e estável Linux 6.18 de
`firelzrd/bore-scheduler`, e a adição de coexistência com `sched_ext` é
acompanhada no mesmo repositório. O resolvedor registra a fonte oficial atual
e só aceita o porte local BORE quando seu SHA-256 coincide com o upstream
revisado; um patch oficial novo interrompe a compilação até que o porte Valve
seja atualizado e validado.
O POC Selector usa um adaptador separado e adaptativo: ele bloqueia os bytes,
commit, caminho, SHA-256 e nome do adaptador da fonte upstream selecionada, e
só aceita as transformações Valve/BORE conhecidas de `rq::poc_idle_committed` e
`select_idle_sibling()`. Ele gera um patch atômico e o verifica com
`git apply --check` antes de alterar a árvore; um hunk upstream alterado é
rejeitado antes da preparação do pacote, em vez de ser aplicado sem validação.

### Outras alterações incluídas

- **Limites do Vangogh:** eleva o máximo exposto de CPU de 3,5 GHz para 4,2 GHz
  e o máximo de PPT informado de 29 W para 50 W.
- **Compilador e CPU:** compilação com Clang/LLVM, Clang LTO completo, Polly e
  Zen 2 como arquitetura mínima de CPU.
- **Patches estáticos:** patches selecionados de Linux-TKG, Gentoo, CachyOS,
  OpenWrt, Qualcomm ath11k e commits fixados do Zen Kernel. Eles incluem, entre
  outros, compatibilidade de compilador e DKMS,
  correções de Wi-Fi e otimizações de compilação.
- **Configuração do kernel:** validação de entrada de áudio, sobrecarga de
  depuração e drivers ou subsistemas legados/sem uso selecionados são
  desabilitados.
- **Ajustes persistentes em tempo de execução:** instala sysctls de VM e
  writeback, configurações de boot para transparent huge pages e MGLRU, KSM
  desabilitado no boot e as configurações de cache de shaders Mesa para a
  sessão Steam.

> **Trade-off de segurança:** o Charcoal define explicitamente
> `CONFIG_CPU_MITIGATIONS=n`. As mitigações de vulnerabilidades de CPU ficam
> desabilitadas; instale-o somente em um dispositivo e modelo de ameaça em que
> essa escolha seja aceitável.

### Módulos incluídos

Estes módulos externos são compilados dentro dos pacotes, portanto não exigem
uma instalação DKMS separada:

| Módulo | Finalidade |
| --- | --- |
| [ryzen_smu](https://github.com/amkillam/ryzen_smu) | Acesso à SMU Ryzen para monitoramento e controles de energia. |
| [xone](https://github.com/dlundqvist/xone) | Driver para dongle sem fio do Xbox One. |
| [xpad-noone](https://github.com/forkymcforkface/xpad-noone) | Permite que xone/xpadneo controlem os dispositivos em vez do driver xpad conflitante. |
| [xpadneo](https://github.com/atar-axis/xpadneo) | Driver avançado para controles Xbox. |

## Instalação

Execute no modo Desktop do SteamOS:
> **Requisito de BIOS no Steam Deck:** antes de instalar, confirme que a opção
> IOMMU está ativa na BIOS. Salve a configuração e reinicie.

```bash
curl -fsSL https://raw.githubusercontent.com/zarpon/linux-charcoal-vulcano/master/install-charcoal.sh -o install-charcoal.sh && bash install-charcoal.sh
```

O instalador da `master` consulta o endpoint estável `/releases/latest` do
GitHub em toda execução. Ele aceita somente uma release Charcoal publicada, que
não seja draft nem pré-release, cuja tag corresponda a
`charcoal-6.18.*-r<run>` e cujo arquivo seja exatamente `linux-${tag}.zip`.
Releases de outras séries de kernel são rejeitadas, sem procurar versões mais
antigas como alternativa. Até a release estável mais recente do Charcoal ser da
série 6.18, o instalador para antes de alterar o sistema. Depois da publicação
de uma release compatível, executar novamente o comando instala essa versão
estável mais recente.
Antes de chamar o `pacman`, o instalador verifica o SHA-256 do ZIP da release e
o SHA-256 de cada pacote interno. Em seguida, ativa o modo de desenvolvedor do
SteamOS sem interação para inicializar o `pacman`, instala os pacotes do kernel
e dos headers Charcoal e atualiza a configuração do bootloader. A ordem de
preferência é `grub-mkconfig`, `steamos-update-grub` e `update-grub`; se nenhum
estiver disponível, o instalador não informa sucesso. Ele reinstala os pacotes
verificados quando necessário, pois revisões de release do Charcoal podem mudar
enquanto a versão-base do kernel da Valve permanece a mesma.

O modo de desenvolvedor permanece ativado após a instalação; somente o sistema
de arquivos raiz do SteamOS volta ao modo somente leitura, inclusive quando a
transação do pacote ou a atualização do bootloader falhar.

Confirme a substituição de `linux-neptune` se o pacman solicitar. Depois,
reinicie e confira:

```bash
uname -a  # deve conter "charcoal"
```

O instalador intencionalmente não redefine o swap zram que já está ativo, pois
o kernel não permite trocar o compressor após a inicialização. O compressor
primário LZ4 e o recompressor ZSTD de prioridade `1` entram em vigor no
primeiro boot com o Charcoal. O ZSTD é fixado no kernel no equivalente a
`zstd --fast=1` (nível de compressão `-1`). Após esse boot, confirme:

```bash
cat /sys/block/zram0/comp_algorithm
cat /sys/block/zram0/recomp_algorithm
```

`[lz4]` indica o compressor primário selecionado. Em `recomp_algorithm`, o
ZSTD aparece na linha de prioridade `1`. Seu equivalente a `--fast=1` é
fixado no porte ZRAM-IR do Charcoal e não pode ser substituído por
`algorithm_params` do espaço de usuário.

Também é possível ver a versão do kernel no modo Jogo em
**Configurações → Sistema**.

![Versão do kernel mostrada no modo Jogo do SteamOS em Configurações → Sistema](https://i.ibb.co/KzRyb2j7/20260525103630-1.jpg)

Atualizações do SteamOS podem substituir o kernel instalado. Após uma
atualização, verifique `uname -a` e execute o instalador novamente se
`charcoal` não aparecer mais.

## Desinstalação

Para remover o Charcoal e voltar ao kernel Neptune padrão:

```bash
sudo steamos-readonly disable
_neptune=$(pacman -Qi $(pacman -Qq 'linux-charcoal*') | awk '/^Replaces/{print $3}')
sudo pacman -Rsn $(pacman -Qq 'linux-charcoal*')
sudo pacman -S "$_neptune"
sudo steamos-readonly enable
```

Depois, reinicie.

## Compilar a partir do código-fonte

O Docker fornece o ambiente Arch Linux esperado para a compilação:

```bash
git clone https://github.com/zarpon/linux-charcoal-vulcano.git
cd linux-charcoal-vulcano
docker build -t linux-charcoal .
docker run --rm -it -v "$PWD:/project" linux-charcoal bash
```

Dentro do container, resolva o conjunto atual de patches antes de compilar:

```bash
cd /project
python3 automation/resolve-latest-patches.py --write
makepkg -s
```

O resolvedor grava os arquivos `latest-*.patch` selecionados, atualiza o
`PKGBUILD` e cria `logs/patch-lock.json`. Revise essas alterações geradas
antes de distribuir uma compilação local. O workflow do GitHub realiza a mesma
resolução e validação de checksums antes de empacotar uma release.

## Compilação manual pelo GitHub

Para gerar uma compilação nova a partir do conjunto atual de patches, sem
alterar o repositório, abra [Build latest SteamOS Charcoal kernel](https://github.com/zarpon/linux-charcoal-vulcano/actions/workflows/push.yml), clique em **Run workflow** e selecione `master`.

- Mantenha **Publish the compiled packages as the latest stable GitHub release**
  ativado para publicar os pacotes verificados como a release estável mais
  recente depois que todas as validações passarem.
- Desative essa opção para apenas validar a compilação. Os pacotes e o lock de
  patches ficarão disponíveis como artefatos do workflow por 14 dias; nenhuma
  release será criada.

Cada execução manual resolve primeiro os patches upstream compatíveis mais
recentes e registra seus commits e SHA-256 exatos em `patch-lock.json`.

Também é possível compilar diretamente em um sistema baseado em Arch. As
dependências incluem `llvm`, `clang`, `lld`, `polly`, `bc`, `cpio`,
`pahole`, `python`, `git` e `openssh`; consulte o `PKGBUILD` para a
lista completa.

## Contribuições

Relate bugs e resultados de compatibilidade de dispositivos no
[rastreador de issues](https://github.com/zarpon/linux-charcoal-vulcano/issues).
Pull requests devem ter como alvo `master`. Para uma mudança de patch ou de
configuração, inclua a origem, a compatibilidade com o kernel-alvo e o
resultado da validação.

## Perfil de compilação e swap

O kernel usa O3. A instalação ativa LZ4 zswap com limite de pool de 50%,
shrinker ativo e swapfile de 150% da RAM na partição de `/home`. ZRAM e
os serviços que o ativam são desativados persistentemente. Consulte
[SWAP.md](SWAP.md) para comportamento, requisitos e verificação.

O tuning usa `vm.vfs_cache_pressure=100`, `vm.dirty_background_ratio=2` e
`vm.dirty_ratio=10`. Os defaults próprios do LRU Marie são preservados.

`CONFIG_ZEN_INTERACTIVE` controla apenas os dois patches Zen existentes:
liberação assíncrona de clientes evdev por RCU e remoção dos selects obrigatórios
de schedutil nos drivers P-State. Nenhum default adicional de memória ou scheduler
Zen é importado. O fsync legado opcode 31 e os patches já upstream de C23/libbpf,
Bluetooth SSP e Qualcomm ath11k não são baixados nem aplicados.

## Ferramentas NAP

Cada build busca as ferramentas mais recentes na branch `main` do NAP e
registra o commit e os hashes usados no pacote.

A instalação preserva automaticamente o aprendizado do NAP entre boots e salva
os pesos a cada 30 minutos. Inclui `napctl` e o visualizador offline
`/usr/share/nap/napviz.html`, gerado com o modelo do kernel compilado. Consulte
[NAP-TOOLS.md](NAP-TOOLS.md) para compatibilidade, comandos e verificação.
