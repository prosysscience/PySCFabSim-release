class EventQueue:
    def __init__(self):
        self.arr = []

    @property
    def first(self):
        return self.arr[0]

    @property
    def empty(self):
        return len(self.arr) == 0

    def pop_first(self):
        return self.arr.pop(0)

    def push(self, item):
        self.arr.append(item)

    def ordered_insert(self, item):
        if len(self.arr) == 0 or item.timestamp < self.arr[0].timestamp:
            self.arr.insert(0, item)
        elif item.timestamp > self.arr[-1].timestamp:
            self.arr.append(item)
        else:
            lo = 0
            hi = len(self.arr)
            while lo < hi:
                mid = (lo + hi) // 2
                if item.timestamp < self.arr[mid].timestamp:
                    hi = mid
                else:
                    lo = mid + 1
            self.arr.insert(lo, item)

    def remove(self, remove):
        self.arr.remove(remove)


class LNode:
    def __init__(self, value, nx):
        self.value = value
        self.next: LNode = nx


class LinkedList:
    def __init__(self):
        self.f = None

    @property
    def first(self):
        return self.f.value

    @property
    def empty(self):
        return self.f is None

    def pop_first(self):
        val = self.f.value
        self.f = self.f.next
        return val

    def ordered_insert(self, item):
        for i, ev in enumerate(self.arr):
            if item.timestamp < ev.timestamp:
                ins = True
                break
        if ins:
            self.arr.insert(i, item)
        else:
            self.push(item)
        pass

    def remove(self, item):
        if item == self.f.value:
            return self.pop_first()
        else:
            pointer = self.f
            while pointer is not None:
                if pointer.next.value == item.value:
                    item = pointer.next.item
                    pointer.next = pointer.next.next
                    return item
            raise ValueError('not found')
