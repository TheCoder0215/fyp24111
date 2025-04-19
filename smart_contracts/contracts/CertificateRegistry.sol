// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";

contract CertificateRegistry is Ownable {
    // Mapping from certificate hash to boolean indicating existence
    mapping(bytes32 => bool) private certificates;
    
    // Mapping to track authorized institutions
    mapping(address => bool) public authorizedInstitutions;
    
    // Events
    event CertificateAdded(bytes32 indexed certificateHash, address indexed institution);
    event InstitutionAuthorized(address indexed institution);
    event InstitutionRevoked(address indexed institution);
    
    // Constructor
    constructor() Ownable(msg.sender) {
        // Initialize contract with deployer as owner
    }
    
    // Modifiers
    modifier onlyAuthorizedInstitution() {
        require(authorizedInstitutions[msg.sender], "Not authorized institution");
        _;
    }
    
    // Institution management
    function authorizeInstitution(address institution) external onlyOwner {
        authorizedInstitutions[institution] = true;
        emit InstitutionAuthorized(institution);
    }
    
    function revokeInstitution(address institution) external onlyOwner {
        authorizedInstitutions[institution] = false;
        emit InstitutionRevoked(institution);
    }
    
    // Certificate management
    function addCertificate(bytes32 certificateHash) external onlyAuthorizedInstitution {
        require(!certificates[certificateHash], "Certificate already exists");
        certificates[certificateHash] = true;
        emit CertificateAdded(certificateHash, msg.sender);
    }
    
    // Query function
    function verifyCertificate(bytes32 certificateHash) external view returns (bool) {
        return certificates[certificateHash];
    }
}