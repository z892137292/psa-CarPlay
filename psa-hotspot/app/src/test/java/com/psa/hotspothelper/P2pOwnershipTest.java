package com.psa.hotspothelper;
import org.junit.Test;
import static org.junit.Assert.*;
public class P2pOwnershipTest {
 @Test public void refusesUnknownOrReplacedGroups(){
  assertFalse(P2pOwnership.canRemove(null,null,true,"DIRECT-a","p2p0"));
  assertFalse(P2pOwnership.canRemove("DIRECT-a","p2p0",true,"DIRECT-b","p2p0"));
  assertFalse(P2pOwnership.canRemove("DIRECT-a","p2p0",true,"DIRECT-a","p2p1"));
  assertFalse(P2pOwnership.canRemove("DIRECT-a","p2p0",false,"DIRECT-a","p2p0"));
  assertFalse(P2pOwnership.canRemove("DIRECT-a",null,true,"DIRECT-a",null));
 }
 @Test public void permitsOnlyThisLifetimesIdentifiedGroupOwner(){assertTrue(P2pOwnership.canRemove("DIRECT-a","p2p0",true,"DIRECT-a","p2p0"));}
}
