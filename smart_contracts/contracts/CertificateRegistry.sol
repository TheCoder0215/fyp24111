// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";

contract CertificateRegistry is Ownable {
    // Mapping from signed certificate hash to boolean indicating existence
    mapping(bytes32 => bool) private signedHashes;

    // Mapping to track authorized institutions
    mapping(address => bool) public authorizedInstitutions;

    // Events
    event SignedHashAdded(bytes32 indexed signedHash, address indexed institution);
    event InstitutionAuthorized(address indexed institution);
    event InstitutionRevoked(address indexed institution);

    // Modifiers
    modifier onlyAuthorizedInstitution() {
        require(authorizedInstitutions[msg.sender], "Not authorized institution");
        _;
    }

    // Constructor
    constructor() Ownable(msg.sender) {
        // The deployer is the owner
    }

    // Authorize a new institution (only owner)
    function authorizeInstitution(address institution) external onlyOwner {
        authorizedInstitutions[institution] = true;
        emit InstitutionAuthorized(institution);
    }

    // Revoke an institution (only owner)
    function revokeInstitution(address institution) external onlyOwner {
        authorizedInstitutions[institution] = false;
        emit InstitutionRevoked(institution);
    }

    // Add a signed certificate hash (only authorized institution)
    function addSignedHash(bytes32 signedHash) external onlyAuthorizedInstitution {
        require(!signedHashes[signedHash], "Signed hash already exists");
        signedHashes[signedHash] = true;
        emit SignedHashAdded(signedHash, msg.sender);
    }

    // Query if a signed hash exists
    function verifySignedHash(bytes32 signedHash) external view returns (bool) {
        return signedHashes[signedHash];
    }
}