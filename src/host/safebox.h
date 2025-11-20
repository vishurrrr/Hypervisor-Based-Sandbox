#pragma once

#include <string>
#include <chrono>
#include <functional>

namespace safebox {

struct VMConfig {
    std::string backend;
    std::string vm_name;
    std::string file_path;
    std::string vm_user;
    int ssh_port;
};

struct CommandResult {
    int return_code;
    std::string stdout;
    std::string stderr;
};

CommandResult execute_command(const std::string &cmd);
bool wait_for_ssh(const std::string &host, int port, int timeout_seconds, 
                  std::function<CommandResult(const std::string&)> exec_fn = nullptr);
int copy_file_to_vm(const std::string &local_path, const std::string &remote_path,
                    const std::string &ssh_target, int ssh_port);
int trigger_agent(const std::string &ssh_target, int ssh_port, 
                  const std::string &file_path, const std::string &output_dir, int timeout);
int download_reports(const std::string &ssh_target, int ssh_port,
                     const std::string &remote_dir, const std::string &local_dir);
int revert_vm(const std::string &backend, const std::string &vm_name);
int start_vm(const std::string &backend, const std::string &vm_name);

} // namespace safebox
