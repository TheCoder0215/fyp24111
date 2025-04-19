const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("CertificateRegistry", function () {
  let registry;
  let owner;
  let institution;
  let other;

  beforeEach(async function () {
    [owner, institution, other] = await ethers.getSigners();
    
    const CertificateRegistry = await ethers.getContractFactory("CertificateRegistry");
    registry = await CertificateRegistry.deploy();
    await registry.deployed();
  });

  it("Should allow owner to authorize institution", async function () {
    await registry.authorizeInstitution(institution.address);
    expect(await registry.authorizedInstitutions(institution.address)).to.be.true;
  });

  it("Should allow authorized institution to add certificate", async function () {
    await registry.authorizeInstitution(institution.address);
    const certificateHash = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("test certificate"));
    
    await registry.connect(institution).addCertificate(certificateHash);
    expect(await registry.verifyCertificate(certificateHash)).to.be.true;
  });
});