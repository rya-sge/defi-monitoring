// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import {IReceiveAssetsGate, ISendSharesGate} from "vault-v2/interfaces/IGate.sol";

/// @title RedemptionWhitelistGate
/// @notice Demo contract for the mainnet-fork crisis (docs/analysis/FORK-PRESENTATION.md, act 5): the redemption gate a
/// curator of a KYC'd RWA vault would plausibly set during a run. Only whitelisted accounts can redeem shares or
/// receive assets from the vault.
/// @dev Mirrors the design of RockawayX's deposit gate `WhitelistSendAssetsGate` (0x51f6…D525): a role setter, a set of
/// whitelisters and a whitelist. That deployed gate cannot be reused for redemptions: it implements only
/// `canSendAssets`, and `canReceiveAssets` on it reverts. Not audited; for a local fork only.
contract RedemptionWhitelistGate is IReceiveAssetsGate, ISendSharesGate {
    address public roleSetter;
    mapping(address => bool) public isWhitelister;
    mapping(address => bool) public isWhitelisted;

    event SetRoleSetter(address indexed roleSetter);
    event SetIsWhitelister(address indexed account, bool isWhitelister);
    event SetIsWhitelisted(address indexed account, bool isWhitelisted);

    error NotRoleSetter();
    error NotWhitelister();

    constructor(address _roleSetter) {
        roleSetter = _roleSetter;
        emit SetRoleSetter(_roleSetter);
    }

    function setRoleSetter(address newRoleSetter) external {
        require(msg.sender == roleSetter, NotRoleSetter());
        roleSetter = newRoleSetter;
        emit SetRoleSetter(newRoleSetter);
    }

    function setIsWhitelister(address account, bool newIsWhitelister) external {
        require(msg.sender == roleSetter, NotRoleSetter());
        isWhitelister[account] = newIsWhitelister;
        emit SetIsWhitelister(account, newIsWhitelister);
    }

    function setIsWhitelisted(address account, bool newIsWhitelisted) external {
        require(isWhitelister[msg.sender], NotWhitelister());
        isWhitelisted[account] = newIsWhitelisted;
        emit SetIsWhitelisted(account, newIsWhitelisted);
    }

    /// @notice Gates `withdraw`/`redeem`: the receiver of the assets must be whitelisted.
    function canReceiveAssets(address account) external view returns (bool) {
        return isWhitelisted[account];
    }

    /// @notice Gates share transfers and redemptions: the owner of the shares must be whitelisted.
    function canSendShares(address account) external view returns (bool) {
        return isWhitelisted[account];
    }
}
