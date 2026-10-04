package com.psa.hotspothelper;
import java.util.Objects;
final class P2pOwnership {
 static boolean canRemove(String ownedName,String ownedInterface,boolean groupOwner,String currentName,String currentInterface){return ownedName!=null&&ownedInterface!=null&&groupOwner&&ownedName.equals(currentName)&&Objects.equals(ownedInterface,currentInterface);}
}
