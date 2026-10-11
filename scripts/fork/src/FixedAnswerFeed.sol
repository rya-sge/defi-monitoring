// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

/// @title FixedAnswerFeed
/// @notice Demo implementation for the RedStone alternative crisis (scripts/fork/alt-redstone.sh): installed behind a
/// RedStone fundamental feed proxy by the Safe that owns its ProxyAdmin, it answers a fixed price. It stands for any
/// code that Safe could install with no timelock; it is not RedStone code. The answer is an immutable, so it needs no
/// storage and cannot collide with the proxy's layout.
contract FixedAnswerFeed {
    int256 public immutable answer;
    uint8 public immutable decimals;

    constructor(int256 _answer, uint8 _decimals) {
        answer = _answer;
        decimals = _decimals;
    }

    function description() external pure returns (string memory) {
        return "fixed answer (fork demo)";
    }

    function latestAnswer() external view returns (int256) {
        return answer;
    }

    function latestRoundData() external view returns (uint80, int256, uint256, uint256, uint80) {
        return (1, answer, block.timestamp, block.timestamp, 1);
    }
}
