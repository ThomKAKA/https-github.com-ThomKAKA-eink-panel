// STEP017D-R1: production SocketOwner exercised via fake syscalls. NOT RUN.
#include "../../hardware/gdey042t81_esp32/src/network_progress/transport.h"
#include <cassert>
#include <type_traits>
#include <initializer_list>
using namespace eink::network_progress;

struct Calls {
  int created = 7, writes = 3, reads = 3;
  bool setup = true, released = true;
  SocketResult connect = SocketResult::Ok, ready = SocketResult::Ok, error = SocketResult::Ok;
  unsigned opens = 0, setups = 0, connects = 0, readiness = 0, errors = 0, closes = 0;
  int openSocket() { ++opens; return created; }
  bool setNonblocking(int fd) { assert(fd == created); ++setups; return setup; }
  SocketResult startConnect(int fd) { assert(fd == created); ++connects; return connect; }
  SocketResult checkReady(int fd) { assert(fd == created); ++readiness; return ready; }
  SocketResult checkError(int fd) { assert(fd == created); ++errors; return error; }
  int writeBytes(int fd, const uint8_t*, size_t) { assert(fd == created); return writes; }
  int readBytes(int fd, uint8_t*, size_t) { assert(fd == created); return reads; }
  bool releaseSocket(int fd) { assert(fd == created); ++closes; return released; }
};
static_assert(!std::is_copy_constructible<SocketOwner<Calls>>::value, "unique owner");
static_assert(!std::is_move_constructible<SocketOwner<Calls>>::value, "no ownership transfer");
int main() {
  {
    Calls c; c.created = -1; SocketOwner<Calls> owner(c);
    assert(owner.begin() == ConnectResult::Failed && !owner.owned());
    assert(owner.finish() && c.closes == 0 && c.setups == 0);
  }
  for (int failure = 0; failure < 4; ++failure) {
    Calls c;
    if (failure == 0) c.setup = false;
    if (failure == 1) c.connect = SocketResult::Failed;
    if (failure >= 2) c.connect = SocketResult::Pending;
    if (failure == 2) c.ready = SocketResult::Failed;
    if (failure == 3) c.error = SocketResult::Failed;
    SocketOwner<Calls> owner(c);
    for (unsigned repeat = 0; repeat < 10; ++repeat) {
      auto result = owner.begin();
      if (result == ConnectResult::Pending) result = owner.poll();
      assert(result == ConnectResult::Failed && !owner.owned());
      assert(c.closes == repeat + 1 && owner.finish());
      assert(c.closes == repeat + 1); // no repeated close after internal cleanup
    }
  }
  {
    Calls c; c.connect = SocketResult::Pending; c.ready = SocketResult::Pending;
    SocketOwner<Calls> owner(c); assert(owner.begin() == ConnectResult::Pending);
    assert(owner.poll() == ConnectResult::Pending && c.errors == 0);
    c.ready = SocketResult::Ok; c.error = SocketResult::Pending;
    assert(owner.poll() == ConnectResult::Pending);
    c.error = SocketResult::Ok; assert(owner.poll() == ConnectResult::Connected);
    uint8_t bytes[8]{};
    for (int n : {kIoPending, kIoFailed, 0, 1, 3}) {
      c.writes = c.reads = n;
      assert(owner.write(bytes, sizeof(bytes)) == n);
      assert(owner.read(bytes, sizeof(bytes)) == n);
    }
    assert(owner.finish() && !owner.owned() && c.closes == 1);
  }
  for (bool setupFailure : {false, true}) {
    Calls c; c.released = false; c.setup = !setupFailure;
    SocketOwner<Calls> owner(c);
    if (setupFailure) assert(owner.begin() == ConnectResult::InvariantFailure);
    else { assert(owner.begin() == ConnectResult::Connected); assert(!owner.finish()); }
    assert(!owner.owned() && !owner.healthy() && c.closes == 1);
    assert(!owner.finish() && c.closes == 1);
    assert(owner.begin() == ConnectResult::InvariantFailure && c.opens == 1);
  }
  {
    Calls c; SocketOwner<Calls> owner(c);
    assert(owner.begin() == ConnectResult::Connected);
    assert(owner.begin() == ConnectResult::InvariantFailure && c.opens == 1);
    assert(!owner.finish() && c.closes == 1 && !owner.owned());
  }
  for (bool reading : {false, true}) {
    Calls c; SocketOwner<Calls> owner(c); uint8_t byte = 0;
    assert((reading ? owner.read(&byte, 1) : owner.write(&byte, 1)) == kIoInvariant);
    assert(!owner.finish() && c.closes == 0);
    assert(owner.begin() == ConnectResult::InvariantFailure && c.opens == 0);
  }
}
