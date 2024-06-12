{
  description = "A basic flake with a shell";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = {
    nixpkgs,
    flake-utils,
    ...
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = nixpkgs.legacyPackages.${system};
    in {
      devShells.default = pkgs.mkShell {
        packages = with pkgs; [
          python3
          python311Packages.playwright
          python311Packages.playwright-stealth
          python311Packages.setuptools
          python311Packages.schedule
          playwright
          uv
          ffmpeg
        ];
        shellHook = ''
          if [ ! -d ".venv" ]; then
              echo "Creating virtual environment..."
              uv venv
          fi
          source ".venv/bin/activate"
          export PLAYWRIGHT_BROWSERS_PATH=${pkgs.playwright-driver.browsers}
          export PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=true
        '';
      };
    });
}
