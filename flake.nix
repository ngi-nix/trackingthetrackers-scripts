{
  description = "Collection of experimental utility scripts for Tracking The Trackers project.";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
    mach-nix-src.url = "github:DavHau/mach-nix";
  };

  outputs = { self, nixpkgs, flake-utils, mach-nix-src }:
    flake-utils.lib.eachDefaultSystem (
      system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          mach-nix = import mach-nix-src { inherit pkgs; python = "python38"; };
          # segfaults currently
          axml2xml = pkgs.buildGoModule {
            pname = "axml2xml";
            src = pkgs.fetchFromGithub {
              owner = "avast";
              repo = "apkparser";
              rev = "6256c76f738e4dc04f5d2cc3e1cc0fbe83d89141";
              sha256 = "0b9gqnfmhkgr95bqw792vi08grv31wibl9zn6v8nviyk6j45a9iw";
            };
            vendorSha256 = null;
            runVend = true;
          };

          pyEnv = mach-nix.mkPython rec {
            requirements = ''
              requests
              github3.py
              xmltodict
              pyasn
              appdirs
              pyyaml
              androguard
            '';
          };
        in
          {
            # defaultPackage = self.packages.${system}.${pname};
            packages = { inherit pkgs; };
            devShell = mach-nix.nixpkgs.mkShell {
              # TODO add axml2xml go package as buildInput
              buildInputs = with pkgs; [ pyEnv fdroidserver jdk11_headless wget curl ];
            };
          }
    );
}
