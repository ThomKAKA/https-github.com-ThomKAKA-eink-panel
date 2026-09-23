#pragma once
#include <cstddef>
#include <cstdint>

namespace eink::network_progress {
enum class ConnectResult { Connected, Pending, Failed, InvariantFailure };
enum class SocketResult { Ok, Pending, Failed };
constexpr int kIoPending = -1, kIoFailed = -2, kIoInvariant = -3;

// Ops is a narrow syscall seam, not another transport. Only this object owns fd.
// Ops receives borrowed descriptors; only releaseSocket may close one on request.
template <class Ops>
class SocketOwner {
 public:
  explicit SocketOwner(Ops& ops) : ops_(ops) {}
  SocketOwner(const SocketOwner&) = delete;
  SocketOwner& operator=(const SocketOwner&) = delete;
  // No destructor cleanup: Machine must explicitly finish each transaction and
  // observe close failure before handoff. The production owner has static life.
  bool owned() const { return fd_ != -1; }
  bool healthy() const { return !faulted_; }

  ConnectResult begin() {
    if (faulted_ || owned()) return invariant();
    fd_ = ops_.openSocket();  // Ownership acquired before any fallible setup.
    if (fd_ < 0) { fd_ = -1; return ConnectResult::Failed; }
    if (!ops_.setNonblocking(fd_)) return failed();
    const auto result = ops_.startConnect(fd_);
    if (result == SocketResult::Failed) return failed();
    connected_ = result == SocketResult::Ok;
    return connected_ ? ConnectResult::Connected : ConnectResult::Pending;
  }
  ConnectResult poll() {
    if (faulted_ || !owned() || connected_) return invariant();
    const auto ready = ops_.checkReady(fd_);
    if (ready == SocketResult::Pending) return ConnectResult::Pending;
    if (ready == SocketResult::Failed) return failed();
    const auto result = ops_.checkError(fd_);
    if (result == SocketResult::Pending) return ConnectResult::Pending;
    if (result == SocketResult::Failed) return failed();
    connected_ = true;
    return ConnectResult::Connected;
  }
  int write(const uint8_t* bytes, size_t size) {
    if (faulted_ || !owned() || !connected_) { invariant(); return kIoInvariant; }
    return ops_.writeBytes(fd_, bytes, size);
  }
  int read(uint8_t* bytes, size_t size) {
    if (faulted_ || !owned() || !connected_) { invariant(); return kIoInvariant; }
    return ops_.readBytes(fd_, bytes, size);
  }
  bool finish() {
    if (owned()) {
      const int borrowed = fd_;
      const bool closed = ops_.releaseSocket(borrowed);
      fd_ = -1; connected_ = false;
      if (!closed) faulted_ = true;
    }
    // A failed close is never retried, even by subsequent finish calls.
    return !faulted_;
  }
 private:
  ConnectResult invariant() { faulted_ = true; return ConnectResult::InvariantFailure; }
  ConnectResult failed() { return finish() ? ConnectResult::Failed : ConnectResult::InvariantFailure; }
  Ops& ops_;
  int fd_ = -1;
  bool connected_ = false, faulted_ = false;
};
}  // namespace eink::network_progress
