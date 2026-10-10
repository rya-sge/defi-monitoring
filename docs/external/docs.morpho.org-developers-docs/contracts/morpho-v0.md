# Morpho Optimizers (Deprecated)

> Source: https://docs.morpho.org/developers/contracts/morpho-v0

---

# Morpho Optimizers (Deprecated)

Morpho V0 has been **deprecated** following the vote of the [MIP 120](https://snapshot.box/#/s:morpho.eth/proposal/0x026c3360d4616532952f5ed0d728daa090dd9a9670c7bf58160cd0709c7d73f8) and [MIP 121](https://snapshot.box/#/s:morpho.eth/proposal/0x60b31cceca2beee55f8845f86b7988ee36f29ad50f5dda636164ab50b561936b).

If you have a position on a Morpho V0 protocol, please reach out via the chatbox on [the Morpho Help Page](https://help.morpho.org/).

[morpho-optimizers](https://github.com/morpho-org/morpho-optimizers)
[morpho-aavev3-optimizer](https://github.com/morpho-org/morpho-aavev3-optimizer)
[morpho-optimizers-vaults](https://github.com/morpho-org/morpho-optimizers-vaults)

## [Morpho V0 deployment addresses](#morpho-v0-deployment-addresses)

| Contract | Address | Source Code |
| --- | --- | --- |
| Morpho V0 (AaveV3 Optimizer - ETH emode) | [ 0x33333aea097c193e66081E930c33020272b33333 ](https://etherscan.io/address/0x33333aea097c193e66081E930c33020272b33333) | [morpho-org/morpho-aavev3-optimizer](https://github.com/morpho-org/morpho-aavev3-optimizer/tree/main) |
| Morpho V0 (AaveV2 Optimizer) | [ 0x777777c9898D384F785Ee44Acfe945efDFf5f3E0 ](https://etherscan.io/address/0x777777c9898D384F785Ee44Acfe945efDFf5f3E0) | [morpho-org/morpho-optimizers](https://github.com/morpho-org/morpho-optimizers) |
| Morpho V0 (AaveV2 Lens) | [ 0x507fa343d0a90786d86c7cd885f5c49263a91ff4 ](https://etherscan.io/address/0x507fA343d0A90786d86C7cd885f5C49263A91FF4) | [morpho-org/morpho-optimizers](https://github.com/morpho-org/morpho-optimizers) |
| Morpho V0 (CompoundV2 Optimizer) | [ 0x8888882f8f843896699869179fB6E4f7e3B58888 ](https://etherscan.io/address/0x8888882f8f843896699869179fB6E4f7e3B58888) | [morpho-org/morpho-optimizers](https://github.com/morpho-org/morpho-optimizers) |
| Morpho V0 (CompoundV2 Lens) | [ 0x930f1b46e1D081Ec1524efD95752bE3eCe51EF67 ](https://etherscan.io/address/0x930f1b46e1D081Ec1524efD95752bE3eCe51EF67) | [morpho-org/morpho-optimizers](https://github.com/morpho-org/morpho-optimizers) |
| Bulker V0 (Gateway) | [ 0xF99e3796f94000462f736925Cf32162Fea82c168 ](https://etherscan.io/address/0xF99e3796f94000462f736925Cf32162Fea82c168) | [morpho-org/morpho-aavev3-optimizer](https://github.com/morpho-org/morpho-aavev3-optimizer/blob/main/src/extensions/BulkerGateway.sol) |

### [Tokenized Supply Vaults](#tokenized-supply-vaults)

ABI are different for Morpho V0 (AaveV2) & Morpho V0 (CompoundV2) vaults, and all the vaults are deployed on the Ethereum mainnet with 18 decimals.
They are fully compliant with the [ERC4626](https://eips.ethereum.org/EIPS/eip-4626) standard.

| Contract | Address | Source Code |
| --- | --- | --- |
| maWBTC | [ 0xd508F85F1511aAeC63434E26aeB6d10bE0188dC7 ](https://etherscan.io/address/0xd508F85F1511aAeC63434E26aeB6d10bE0188dC7) | [morpho-optimizers-vaults](https://github.com/morpho-org/morpho-optimizers-vaults) |
| maWETH | [ 0x490BBbc2485e99989Ba39b34802faFa58e26ABa4 ](https://etherscan.io/address/0x490BBbc2485e99989Ba39b34802faFa58e26ABa4) | [morpho-optimizers-vaults](https://github.com/morpho-org/morpho-optimizers-vaults) |
| maDAI | [ 0x36F8d0D0573ae92326827C4a82Fe4CE4C244cAb6 ](https://etherscan.io/address/0x36F8d0D0573ae92326827C4a82Fe4CE4C244cAb6) | [morpho-optimizers-vaults](https://github.com/morpho-org/morpho-optimizers-vaults) |
| maUSDC | [ 0xA5269A8e31B93Ff27B887B56720A25F844db0529 ](https://etherscan.io/address/0xA5269A8e31B93Ff27B887B56720A25F844db0529) | [morpho-optimizers-vaults](https://github.com/morpho-org/morpho-optimizers-vaults) |
| maUSDT | [ 0xAFe7131a57E44f832cb2dE78ade38CaD644aaC2f ](https://etherscan.io/address/0xAFe7131a57E44f832cb2dE78ade38CaD644aaC2f) | [morpho-optimizers-vaults](https://github.com/morpho-org/morpho-optimizers-vaults) |
| maCRV | [ 0x9dc7094530cB1bcf5442c3b9389ee386738A190c ](https://etherscan.io/address/0x9dc7094530cB1bcf5442c3b9389ee386738A190c) | [morpho-optimizers-vaults](https://github.com/morpho-org/morpho-optimizers-vaults) |
| mcDAI | [ 0x8F88EaE3e1c01d60bccdc3DB3CBD5362Dd55d707 ](https://etherscan.io/address/0x8F88EaE3e1c01d60bccdc3DB3CBD5362Dd55d707) | [morpho-optimizers-vaults](https://github.com/morpho-org/morpho-optimizers-vaults) |
| mcWETH | [ 0x676E1B7d5856f4f69e10399685e17c2299370E95 ](https://etherscan.io/address/0x676E1B7d5856f4f69e10399685e17c2299370E95) | [morpho-optimizers-vaults](https://github.com/morpho-org/morpho-optimizers-vaults) |
| mcCOMP | [ 0xaA768b85eC827cCc36D882c1814bcd27ec4A8593 ](https://etherscan.io/address/0xaA768b85eC827cCc36D882c1814bcd27ec4A8593) | [morpho-optimizers-vaults](https://github.com/morpho-org/morpho-optimizers-vaults) |
| mcUNI | [ 0x496da625C736a2fF122638Dc26dCf1bFdEf1778c ](https://etherscan.io/address/0x496da625C736a2fF122638Dc26dCf1bFdEf1778c) | [morpho-optimizers-vaults](https://github.com/morpho-org/morpho-optimizers-vaults) |
| mcUSDC | [ 0xba9E3b3b684719F80657af1A19DEbc3C772494a0 ](https://etherscan.io/address/0xba9E3b3b684719F80657af1A19DEbc3C772494a0) | [morpho-optimizers-vaults](https://github.com/morpho-org/morpho-optimizers-vaults) |
| mcUSDT | [ 0xC2A4fBA93d4120d304c94E4fd986e0f9D213eD8A ](https://etherscan.io/address/0xC2A4fBA93d4120d304c94E4fd986e0f9D213eD8A) | [morpho-optimizers-vaults](https://github.com/morpho-org/morpho-optimizers-vaults) |
| mcWBTC | [ 0xF31AC95fe692190b9C67112d8c912bA9973944F2 ](https://etherscan.io/address/0xF31AC95fe692190b9C67112d8c912bA9973944F2) | [morpho-optimizers-vaults](https://github.com/morpho-org/morpho-optimizers-vaults) |
| ma3WETH | [ 0x39Dd7790e75C6F663731f7E1FdC0f35007D3879b ](https://etherscan.io/address/0x39Dd7790e75C6F663731f7E1FdC0f35007D3879b) | [morpho-aavev3-optimizer](https://github.com/morpho-org/morpho-aavev3-optimizer/blob/main/src/extensions/SupplyVault.sol) |

## [Audits and Formal Verification](#audits-and-formal-verification)

Morpho is known for its industry-leading security practices and follows a multi-faceted approach to security.

Morpho security practices include formal verification, mutation tests, fuzzing, unit testing, and peer reviews that can be found within respective [Github repositories](https://github.com/morpho-org). External measures include professional security reviews, contests, and pre/post-deployment bounties.

A whole article was dedicated to the [Morpho Security Framework](https://morpho.org/blog/morpho-blue-security-framework-building-the-most-secure-lending-protocol/).

The full list of audits and formal verifications is available below.

### [Audits](#audits)

| Auditors | Scope | Date | Report |
| --- | --- | --- | --- |
| [Spearbit](https://spearbit.com/) | Morpho V0 (AaveV3) | 2023-06-19 | [spearbit-report](https://cdn.morpho.org/documents/Spearbit_19062023.pdf) |
| [Spearbit](https://spearbit.com/) | Morpho V0 (AaveV3) | 2023-05-04 | [spearbit-report](https://cdn.morpho.org/documents/Spearbit_04052023.pdf) |
| [Runtime Verification](https://runtimeverification.com/) | Morpho V0 (AaveV3) | 2023-05-02 | [runtime-verification-report](https://cdn.morpho.org/documents/Runtime_02052023.pdf) |
| [Spearbit](https://spearbit.com/) | Morpho V0 | 2023-03-01 | [spearbit-report](https://cdn.morpho.org/documents/Spearbit_010323.pdf) |
| [Pessimistic](https://pessimistic.io/) | Morpho V0 | 2023-02-20 | [pessimistic-report](https://cdn.morpho.org/documents/Pessimistic_200223.pdf) |
| [Spearbit](https://spearbit.com/) | Morpho V0 [Draft] | 2022-12-06 | [spearbit-draft-report](https://cdn.morpho.org/documents/Spearbit_morpho_draft_061222.pdf) |
| [Pessimistic](https://pessimistic.io/) | Morpho V0 | 2022-10-06 | [pessimistic-report](https://cdn.morpho.org/documents/Pessimistic_061022.pdf) |
| [Omniscia](https://omniscia.io/) | Morpho V0 | 2022-08-25 | [omniscia-report](https://omniscia.io/reports/morpho-labs-tokenized-vaults/) |
| [Spearbit](https://spearbit.com/) | Morpho V0 (AaveV2) | 2022-08-24 | [spearbit-report](https://cdn.morpho.org/documents/MorphoAaveV2_Audit_Spearbit.pdf) |
| [Chainsecurity](https://chainsecurity.com/) | Morpho V0 (AaveV3) [Non Ethereum] | 2022-08-19 | [chainsecurity-report](https://cdn.morpho.org/documents/MorphoAaveV3_Audit_ChainSecurity.pdf) |
| [Omniscia](https://omniscia.io/) | Morpho Datastructures | 2022-08-17 | [omniscia-report](https://cdn.morpho.org/documents/MorphoAaveV2_Audit_Omniscia.pdf) |
| [Pessimistic](https://pessimistic.io/) | Morpho V0 (AaveV2) | 2022-07-25 | [pessimistic-report](https://cdn.morpho.org/documents/MorphoAaveV2_Audit_Pessimistic.pdf) |
| [Trail of Bits](https://www.trailofbits.com/) | Morpho V0 (CompoundV2) | 2022-07-21 | [trail-of-bits-report](https://cdn.morpho.org/documents/TrailOfBits_210722.pdf) |
| [Trail of Bits](https://www.trailofbits.com/) | Morpho V0 (CompoundV2) | 2022-06-03 | [trail-of-bits-report](https://cdn.morpho.org/documents/TrailOfBits_030622.pdf) |
| [Spearbit](https://spearbit.com/) | Morpho V0 (AaveV2) | 2022-09-05 | [spearbit-report](https://cdn.morpho.org/documents/Spearbit_090522.pdf) |
| [Pessimistic](https://pessimistic.io/) | [Beta] Morpho V0 (CompoundV2) | 2022-04-25 | [pessimistic-report](https://cdn.morpho.org/documents/Pessimistic_250422.pdf) |
| [Pessimistic](https://pessimistic.io/) | [Beta] Morpho V0 (AaveV2) | 2022-03-08 | [pessimistic-report](https://cdn.morpho.org/documents/Pessimistic_080322.pdf) |
| [Pessimistic](https://pessimistic.io/) | [Beta] Morpho V0 (AaveV2) | 2022-02-16 | [pessimistic-report](https://cdn.morpho.org/documents/pessimistic_160222.pdf) |
| [Pessimistic](https://pessimistic.io/) | [Alpha] Morpho V0 (AaveV2) | 2022-01-11 | [pessimistic-report](https://cdn.morpho.org/documents/Pessimistic_110122.pdf) |
| [Solidified](https://www.solidified.io/) | [Alpha] Morpho V0 (CompoundV2) | 2021-11-04 | [solidified-report](https://cdn.morpho.org/documents/Solidified_041121.pdf) |
| [Lexfo](https://lexfo.fr/) | Morpho-related DNS's & Morpho-related Github's | 2023-05-10 | [Lexfo_250523.pdf](https://cdn.morpho.org/documents/Lexfo_250523.pdf) |
| [Securing](https://www.securing.biz/) | [Beta] Morpho Association dApp | 2022-04-04 | [MorphoDAO_Frontend_04042022.pdf](https://cdn.morpho.org/documents/MorphoDAO_Frontend_04042022.pdf) |

### [Formal verifications](#formal-verifications)

| Formally Proven | Scope | Date | Tool Used |
| --- | --- | --- | --- |
| [Morpho V0 (AaveV3)](https://github.com/morpho-org/morpho-aavev3-optimizer/tree/main/why3) | core logic | April 2023 | [Why3](https://www.why3.org/) |
| [Morpho V0](https://github.com/morpho-org/morpho-optimizers/tree/main/certora) | Merkle tree and claim function | April 2024 | [Certora](https://www.certora.com/) & custom checker |
| [Morpho utils](https://github.com/morpho-org/morpho-utils/tree/main/certora) | math functions | December 2022 | [Certora](https://www.certora.com/) |
| [Morpho data structures](https://github.com/morpho-org/morpho-data-structures/tree/main/certora) | double linked list and log buckets | January 2023 | [Certora](https://www.certora.com/) & [Halmos](https://github.com/a16z/halmos) |

[Universal Rewards Distributors (Deprecated)

Previous Page

](https://docs.morpho.org/developers/contracts/rewards/)[Get Started

Connect Claude Code, Codex, or Cursor to Morpho — query vaults, markets, and positions, and prepare unsigned transactions from your agent.

](https://docs.morpho.org/developers/agents/get-started/)