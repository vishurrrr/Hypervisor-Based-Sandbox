#include <gtest/gtest.h>
#include "safebox.h"

using namespace safebox;

// Mock execute_command for testing
static bool mock_ssh_success = true;
CommandResult mock_execute(const std::string& cmd) {
    CommandResult res{0, "", ""};
    if (cmd.find("echo ok") != std::string::npos) {
        res.return_code = mock_ssh_success ? 0 : 1;
    }
    return res;
}

TEST(SafeBoxTests, WaitForSSH_Success) {
    mock_ssh_success = true;
    bool result = wait_for_ssh("user@127.0.0.1", 2222, 5, mock_execute);
    EXPECT_TRUE(result);
}

TEST(SafeBoxTests, WaitForSSH_Timeout) {
    mock_ssh_success = false;
    bool result = wait_for_ssh("user@127.0.0.1", 2222, 1, mock_execute);
    EXPECT_FALSE(result);
}

TEST(SafeBoxTests, CommandExecution) {
    CommandResult res = execute_command("echo test");
    EXPECT_EQ(res.return_code, 0);
}

TEST(SafeBoxTests, RevertVM_VirtualBox) {
    int rc = revert_vm("virtualbox", "test-vm");
    EXPECT_NE(rc, -1);
}

TEST(SafeBoxTests, RevertVM_KVM) {
    int rc = revert_vm("kvm", "test-vm");
    EXPECT_NE(rc, -1);
}

TEST(SafeBoxTests, StartVM_InvalidBackend) {
    int rc = start_vm("invalid", "test-vm");
    EXPECT_EQ(rc, 1);
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
