// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

/// @title MGloEuroFeedV2
/// @notice Demo implementation for the mainnet-fork crisis (docs/analysis/FORK-PRESENTATION.md, act 6), installed
/// behind the mGLOeuro/EUR feed proxy (0x8b7b…9609) through the Midas timelock. It is NOT Midas code.
/// @dev The deployed `MGloEuroCustomAggregatorFeed` fixes its band at [90,000; 110,000] EUR with no setter, so a fund
/// loss above 10 % can only reach the oracle through an upgrade, behind the 48 h `MidasTimelockController`. This
/// implementation stands for the one Midas would install: same Chainlink-style interface (8 decimals), a wider band,
/// and the same single writer (the feed-admin EOA, here an immutable). Its storage sits in its own ERC-7201 namespace,
/// so it cannot collide with the old layout; rounds before the upgrade are not readable through it.
contract MGloEuroFeedV2 {
    /// @custom:storage-location erc7201:riskdep.fork.MGloEuroFeedV2
    struct Layout {
        uint80 latestRound;
        mapping(uint80 => int256) answers;
        mapping(uint80 => uint256) timestamps;
    }

    // keccak256(abi.encode(uint256(keccak256("riskdep.fork.MGloEuroFeedV2")) - 1)) & ~bytes32(uint256(0xff))
    bytes32 private constant LAYOUT = 0xe7f489c11ec7864fedd8abf84e50697022b75383b798a08415641d3cdc89ca00;

    address public immutable feedAdmin;
    int192 public immutable minAnswer;
    int192 public immutable maxAnswer;

    event AnswerUpdated(int256 indexed current, uint256 indexed roundId, uint256 updatedAt);

    error NotFeedAdmin();
    error OutOfBand();
    error NoData();

    constructor(address _feedAdmin, int192 _minAnswer, int192 _maxAnswer) {
        feedAdmin = _feedAdmin;
        minAnswer = _minAnswer;
        maxAnswer = _maxAnswer;
    }

    function _l() private pure returns (Layout storage l) {
        bytes32 slot = LAYOUT;
        assembly {
            l.slot := slot
        }
    }

    function setRoundData(int256 data) external {
        require(msg.sender == feedAdmin, NotFeedAdmin());
        require(data >= minAnswer && data <= maxAnswer, OutOfBand());
        Layout storage l = _l();
        uint80 id = l.latestRound + 1;
        l.latestRound = id;
        l.answers[id] = data;
        l.timestamps[id] = block.timestamp;
        emit AnswerUpdated(data, id, block.timestamp);
    }

    function decimals() external pure returns (uint8) {
        return 8;
    }

    function description() external pure returns (string memory) {
        return "mGLOeuro/EUR";
    }

    function version() external pure returns (uint256) {
        return 2;
    }

    function latestRound() external view returns (uint256) {
        return _l().latestRound;
    }

    function getRoundData(uint80 roundId) public view returns (uint80, int256, uint256, uint256, uint80) {
        Layout storage l = _l();
        uint256 ts = l.timestamps[roundId];
        require(ts != 0, NoData());
        return (roundId, l.answers[roundId], ts, ts, roundId);
    }

    function latestRoundData() external view returns (uint80, int256, uint256, uint256, uint80) {
        return getRoundData(_l().latestRound);
    }
}
