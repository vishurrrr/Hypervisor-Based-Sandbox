#include "safebox.h"
#include <iostream>
#include <string>
#include <sstream>
#include <filesystem>

using namespace safebox;

int main(int argc, char** argv) {
    if (argc < 7) {
        std::cerr << "Usage: safebox-host --backend <virtualbox|kvm> --vm-name <name> --file <path> --user <vmuser> [--ssh-port <port>]" << std::endl;
        return 1;
    }

    std::string backend;
    std::string vm_name;
    std::string file_path;
    std::string vm_user = "safebox";
    int ssh_port = 2222;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--backend") backend = argv[++i];
        else if (arg == "--vm-name") vm_name = argv[++i];
        else if (arg == "--file") file_path = argv[++i];
        else if (arg == "--user") vm_user = argv[++i];
        else if (arg == "--ssh-port") ssh_port = std::stoi(argv[++i]);
    }

    if (backend.empty() || vm_name.empty() || file_path.empty()) {
        std::cerr << "Missing required args." << std::endl;
        return 2;
    }

    // 1) Start VM
    if (start_vm(backend, vm_name) != 0) return 3;

    // 2) Wait for SSH
    std::string ssh_target = vm_user + "@127.0.0.1";
    std::cout << "Waiting for SSH at 127.0.0.1:" << ssh_port << std::endl;
    if (!wait_for_ssh(ssh_target, ssh_port, 120)) {
        std::cerr << "SSH did not become available within timeout." << std::endl;
        return 5;
    }
    std::cout << "SSH reachable. Copying file to VM..." << std::endl;

    // 3) Copy file to VM
    std::filesystem::path p(file_path);
    std::string filename = p.filename();
    if (copy_file_to_vm(file_path, "/home/" + vm_user + "/incoming/" + filename, ssh_target, ssh_port) != 0) {
        std::cerr << "SCP failed." << std::endl;
        return 6;
    }

    // 4) Trigger agent
    if (trigger_agent(ssh_target, ssh_port, "/home/" + vm_user + "/incoming/" + filename, 
                      "/home/" + vm_user + "/out", 120) != 0) {
        std::cerr << "Failed to trigger agent remotely." << std::endl;
    }

    // 5) Download reports
    std::cout << "Downloading reports..." << std::endl;
    download_reports(ssh_target, ssh_port, "/home/" + vm_user + "/out", "./reports");

    // 6) Revert VM
    if (revert_vm(backend, vm_name) != 0) {
        std::cerr << "Failed to revert VM." << std::endl;
        return 7;
    }

    std::cout << "Analysis finished. Reports (if any) are in ./reports/" << std::endl;
    return 0;
}
