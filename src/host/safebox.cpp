#include "safebox.h"
#include <cstdlib>
#include <iostream>
#include <sstream>
#include <thread>
#include <filesystem>

using namespace std::chrono_literals;

namespace safebox {

CommandResult execute_command(const std::string &cmd) {
    CommandResult result{-1, "", ""};
    std::cerr << "[cmd] " << cmd << std::endl;
    int rc = std::system(cmd.c_str());
    result.return_code = rc;
    return result;
}

bool wait_for_ssh(const std::string &host, int port, int timeout_seconds,
                  std::function<CommandResult(const std::string&)> exec_fn) {
    if (!exec_fn) {
        exec_fn = execute_command;
    }
    int waited = 0;
    while (waited < timeout_seconds) {
        std::ostringstream cmd;
        cmd << "ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -p " << port
            << " " << host << " echo ok 2>/dev/null";
        CommandResult res = exec_fn(cmd.str());
        if (res.return_code == 0) return true;
        std::this_thread::sleep_for(2s);
        waited += 2;
    }
    return false;
}

int copy_file_to_vm(const std::string &local_path, const std::string &remote_path,
                    const std::string &ssh_target, int ssh_port) {
    std::ostringstream scp_cmd;
    scp_cmd << "scp -P " << ssh_port << " -o StrictHostKeyChecking=no "
            << local_path << " " << ssh_target << ":" << remote_path;
    CommandResult res = execute_command(scp_cmd.str());
    return res.return_code;
}

int trigger_agent(const std::string &ssh_target, int ssh_port,
                  const std::string &file_path, const std::string &output_dir, int timeout) {
    std::ostringstream remote_cmd;
    remote_cmd << "ssh -p " << ssh_port << " -o StrictHostKeyChecking=no " << ssh_target
               << " \"nohup python3 /home/safebox/agent/agent.py --file " << file_path
               << " --output " << output_dir << " --timeout " << timeout << " &> " << output_dir << "/agent-run.log &\"";
    CommandResult res = execute_command(remote_cmd.str());
    return res.return_code;
}

int download_reports(const std::string &ssh_target, int ssh_port,
                     const std::string &remote_dir, const std::string &local_dir) {
    std::filesystem::create_directories(local_dir);
    std::ostringstream scp_cmd;
    scp_cmd << "scp -P " << ssh_port << " -o StrictHostKeyChecking=no "
            << ssh_target << ":" << remote_dir << "/report-*.json " << local_dir << "/";
    CommandResult res = execute_command(scp_cmd.str());
    return res.return_code;
}

int revert_vm(const std::string &backend, const std::string &vm_name) {
    CommandResult res{0, "", ""};
    if (backend == "virtualbox") {
        std::ostringstream cmd1;
        cmd1 << "VBoxManage controlvm " << vm_name << " poweroff";
        res = execute_command(cmd1.str());
        if (res.return_code != 0) return res.return_code;
        
        std::ostringstream cmd2;
        cmd2 << "VBoxManage snapshot " << vm_name << " restore clean";
        res = execute_command(cmd2.str());
    } else if (backend == "kvm") {
        std::ostringstream cmd1;
        cmd1 << "virsh destroy " << vm_name;
        res = execute_command(cmd1.str());
        if (res.return_code != 0) return res.return_code;
        
        std::ostringstream cmd2;
        cmd2 << "virsh snapshot-revert " << vm_name << " clean";
        res = execute_command(cmd2.str());
    }
    return res.return_code;
}

int start_vm(const std::string &backend, const std::string &vm_name) {
    CommandResult res{0, "", ""};
    if (backend == "virtualbox") {
        std::ostringstream cmd;
        cmd << "VBoxManage startvm " << vm_name << " --type headless";
        res = execute_command(cmd.str());
    } else if (backend == "kvm") {
        std::ostringstream cmd;
        cmd << "virsh start " << vm_name;
        res = execute_command(cmd.str());
    } else {
        return 1;
    }
    return res.return_code;
}

} // namespace safebox
