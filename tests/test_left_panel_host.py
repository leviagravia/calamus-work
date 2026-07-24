import unittest
from calamus_left_panel import LeftPanelHost

class Widget:
    def __init__(self): self.parent=None; self.visible=False; self.size_request=None
    def get_parent(self): return self.parent
    def show_all(self): self.visible=True
    def set_size_request(self,*a): self.size_request=a
    def set_hexpand(self,*a): pass
    def set_vexpand(self,*a): pass
class Allocation: width=1000
class Paned:
    def __init__(self): self.child=None; self.pack_args=None
    def pack1(self,w,*a): self.child=w; self.pack_args=a; w.parent=self
    def remove(self,w): self.child=None; w.parent=None
    def get_allocation(self): return Allocation()
    def set_position(self,p): self.position=p

class LeftPanelHostTests(unittest.TestCase):
    def test_exactly_two_clients_share_one_slot(self):
        paned=Paned(); host=LeftPanelHost(paned,lambda:None)
        nav=Widget(); work=Widget(); n=host.register("navigator",nav); w=host.register("workspace",work)
        events=[]; n.subscribe(lambda v: events.append(("n",v))); w.subscribe(lambda v: events.append(("w",v)))
        n.show(); self.assertIs(paned.child,nav)
        w.show(); self.assertIs(paned.child,work); self.assertIsNone(nav.parent)
        self.assertIn(("n",False),events); self.assertIn(("w",True),events)
        with self.assertRaises(KeyError): host.register("third",Widget())

    def test_side_panel_is_shrinkable_and_does_not_export_fixed_window_minimum(self):
        paned=Paned(); host=LeftPanelHost(paned,lambda:None)
        widget=Widget(); client=host.register("workspace",widget)
        client.show()
        self.assertEqual(paned.pack_args,(False,True))
        self.assertEqual(widget.size_request,(-1,-1))
        self.assertEqual(paned.position,248)

if __name__ == "__main__": unittest.main()
